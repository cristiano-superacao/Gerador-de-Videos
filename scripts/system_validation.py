import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
from sqlalchemy import inspect


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.database import engine  # noqa: E402


def print_check(name: str, ok: bool, detail: str) -> None:
    status = "ok" if ok else "fail"
    print(f"[{status}] {name}: {detail}")


def validate_variables() -> list[str]:
    failures = []
    print_check(
        "settings.app_name",
        bool(settings.app_name),
        settings.app_name,
    )
    print_check("settings.app_env", bool(settings.app_env), settings.app_env)
    print_check(
        "settings.secret_key",
        bool(settings.secret_key),
        "configured" if bool(settings.secret_key) else "missing",
    )
    print_check(
        "settings.database_url",
        bool(settings.database_url),
        settings.database_url.split("?")[0],
    )

    if not settings.secret_key:
        failures.append("settings.secret_key")
    if not settings.database_url:
        failures.append("settings.database_url")

    return failures


def validate_tables() -> list[str]:
    failures = []
    session = SessionLocal()
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        required_tables = {"users", "video_jobs"}
        missing_tables = sorted(required_tables - tables)
        print_check(
            "database.tables",
            not missing_tables,
            ", ".join(sorted(tables)),
        )
        if missing_tables:
            failures.extend([f"table:{name}" for name in missing_tables])

        if "video_jobs" in tables:
            columns = {
                column["name"]
                for column in inspector.get_columns("video_jobs")
            }
            required_columns = {
                "user_id",
                "status",
                "provider",
                "requested_provider",
                "render_id",
                "output_url",
                "status_message",
            }
            missing_columns = sorted(required_columns - columns)
            print_check(
                "database.video_jobs_columns",
                not missing_columns,
                ", ".join(sorted(columns)),
            )
            if missing_columns:
                failures.extend(
                    [f"video_jobs:{name}" for name in missing_columns]
                )
    finally:
        session.close()

    return failures


def validate_pages_and_apis() -> list[str]:
    base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
    email = os.getenv(
        "TEST_APP_USER_EMAIL",
        f"validation.{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
    )
    password = os.getenv("TEST_APP_USER_PASSWORD", "18042016")
    failures = []

    with httpx.Client(
        base_url=base_url,
        follow_redirects=True,
        timeout=60.0,
    ) as client:
        checks = [
            ("home", client.get("/"), 200),
            ("how_to_use", client.get("/como-usar"), 200),
            ("login_page", client.get("/login"), 200),
            ("register_page", client.get("/register"), 200),
        ]
        for name, response, expected in checks:
            ok = response.status_code == expected
            print_check(name, ok, f"status={response.status_code}")
            if not ok:
                failures.append(name)

        home_html = checks[0][1].text
        how_to_use_html = checks[1][1].text
        responsive_markers = [
            "<meta name=\"viewport\"",
            "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8",
            "grid lg:grid-cols-2 gap-8 items-center",
            "grid lg:grid-cols-2 gap-4 sm:gap-5",
        ]
        missing_markers = [
            marker
            for marker in responsive_markers
            if marker not in home_html and marker not in how_to_use_html
        ]
        print_check(
            "responsive_markers",
            not missing_markers,
            (
                "all-present"
                if not missing_markers
                else ", ".join(missing_markers)
            ),
        )
        if missing_markers:
            failures.append("responsive_markers")

        register_response = client.post(
            "/register",
            data={"email": email, "password": password},
        )
        print_check(
            "register_action",
            register_response.status_code == 200,
            f"status={register_response.status_code}",
        )
        if register_response.status_code != 200:
            failures.append("register_action")

        login_response = client.post(
            "/login",
            data={"email": email, "password": password},
        )
        print_check(
            "login_action",
            login_response.status_code == 200,
            f"status={login_response.status_code}",
        )
        if login_response.status_code != 200:
            failures.append("login_action")

        dashboard_response = client.get("/dashboard")
        print_check(
            "dashboard_page",
            dashboard_response.status_code == 200,
            f"status={dashboard_response.status_code}",
        )
        if dashboard_response.status_code != 200:
            failures.append("dashboard_page")

        generation_response = client.post(
            "/generation/create",
            data={
                "source_type": "text",
                "source_content": "Validação sistêmica do gerador de vídeos",
            },
        )
        print_check(
            "generation_text",
            generation_response.status_code == 200,
            f"status={generation_response.status_code}",
        )
        if generation_response.status_code != 200:
            failures.append("generation_text")

        jobs_live_response = client.get("/dashboard/jobs/live")
        print_check(
            "jobs_live",
            jobs_live_response.status_code == 200,
            f"status={jobs_live_response.status_code}",
        )
        if jobs_live_response.status_code != 200:
            failures.append("jobs_live")

        if jobs_live_response.status_code == 200:
            jobs_payload = jobs_live_response.json()
            has_jobs_key = "jobs" in jobs_payload
            print_check(
                "jobs_live_payload",
                has_jobs_key,
                (
                    "keys=" + ", ".join(sorted(jobs_payload.keys()))
                    if has_jobs_key
                    else "payload-sem-jobs"
                ),
            )
            if not has_jobs_key:
                failures.append("jobs_live_payload")
            elif jobs_payload["jobs"]:
                first_job = jobs_payload["jobs"][0]
                has_operational_fields = all(
                    field in first_job
                    for field in [
                        "provider",
                        "requested_provider",
                        "status_message",
                    ]
                )
                print_check(
                    "jobs_live_operational_fields",
                    has_operational_fields,
                    ", ".join(sorted(first_job.keys())),
                )
                if not has_operational_fields:
                    failures.append("jobs_live_operational_fields")

    return failures


def main() -> int:
    failures = []
    failures.extend(validate_variables())
    failures.extend(validate_tables())
    failures.extend(validate_pages_and_apis())

    if failures:
        print("system-validation:fail")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("system-validation:ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
