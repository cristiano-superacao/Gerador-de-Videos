import os
import re
import sys
from datetime import datetime
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def assert_status(response: httpx.Response, expected: int, name: str) -> None:
    if response.status_code != expected:
        raise RuntimeError(
            f"{name} failed: expected {expected}, got {response.status_code}"
        )


def get_user_id_from_admin_page(html: str, email: str) -> int:
    normalized_email = email.lower().strip()
    rows = re.findall(
        r"<tr[^>]*>(.*?)</tr>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    for row in rows:
        if normalized_email not in row.lower():
            continue

        match = re.search(
            r'action="/admin/users/(\d+)/credits"',
            row,
            flags=re.IGNORECASE,
        )
        if match:
            return int(match.group(1))

    raise RuntimeError(f"user lookup failed via admin page: {email}")


def ensure_user_session(
    client: httpx.Client,
    email: str,
    password: str,
) -> None:
    response = client.post(
        "/login",
        data={"email": email, "password": password},
    )

    if response.status_code == 200:
        return

    register_response = client.post(
        "/register",
        data={"email": email, "password": password},
    )
    assert_status(register_response, 200, "register")

    response = client.post(
        "/login",
        data={"email": email, "password": password},
    )
    assert_status(response, 200, "login")


def main() -> None:
    base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
    default_email = "cristiano.s.santos@ba.estudante.senai.br"
    if base_url.startswith("https://"):
        default_email = (
            "smoke.railway."
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
        )

    email = os.getenv(
        "TEST_APP_USER_EMAIL",
        default_email,
    )
    password = os.getenv("TEST_APP_USER_PASSWORD", "18042016")
    admin_email = os.getenv("TEST_ADMIN_EMAIL", "admin@agentesia.com")
    admin_password = os.getenv("TEST_ADMIN_PASSWORD", "admin123")
    with httpx.Client(
        base_url=base_url,
        follow_redirects=True,
        timeout=60.0,
    ) as client:
        response = client.get("/")
        assert_status(response, 200, "home")

        response = client.get("/como-usar")
        assert_status(response, 200, "how-to")

        ensure_user_session(client, email, password)

        response = client.get("/dashboard")
        assert_status(response, 200, "dashboard")

        response = client.post(
            "/generation/create",
            data={
                "source_type": "text",
                "source_content": "Tendências de IA para indústria em 2026",
            },
        )
        assert_status(response, 200, "generation-text")

        response = client.post(
            "/generation/create",
            data={
                "source_type": "link",
                "source_content": "https://example.com/insights-ia-manufatura",
            },
        )
        assert_status(response, 200, "generation-link")

        response = client.post(
            "/generation/create",
            data={
                "source_type": "video",
                "source_content": "",
            },
            files={
                "source_file": (
                    "amostra.mp3",
                    b"fake-audio-content",
                    "audio/mpeg",
                ),
            },
        )
        assert_status(response, 200, "generation-video")

        response = client.get("/dashboard/jobs/live")
        assert_status(response, 200, "jobs-live")
        payload = response.json()
        if "jobs" not in payload:
            raise RuntimeError("jobs-live failed: payload sem campo jobs")

        response = client.post("/logout")
        assert_status(response, 200, "logout")

        response = client.post(
            "/login",
            data={"email": admin_email, "password": admin_password},
        )
        assert_status(response, 200, "login-admin")

        response = client.get("/admin/users")
        assert_status(response, 200, "admin-users")
        user_id = get_user_id_from_admin_page(response.text, email)

        response = client.post(
            f"/admin/users/{user_id}/credits",
            data={"credits": 50},
        )
        assert_status(response, 200, "admin-update-credits")

        response = client.post("/logout")
        assert_status(response, 200, "logout-admin")

    print("client-smoke-test:ok")


if __name__ == "__main__":
    main()
