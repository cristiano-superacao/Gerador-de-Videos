import os
import sys
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


def main() -> None:
    base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
    email = os.getenv(
        "TEST_APP_USER_EMAIL",
        "cristiano.s.santos@ba.estudante.senai.br",
    )
    password = os.getenv("TEST_APP_USER_PASSWORD", "18042016")

    with httpx.Client(base_url=base_url, follow_redirects=True, timeout=60.0) as client:
        response = client.get("/")
        assert_status(response, 200, "home")

        response = client.get("/como-usar")
        assert_status(response, 200, "how-to")

        response = client.post(
            "/login",
            data={"email": email, "password": password},
        )
        assert_status(response, 200, "login")

        response = client.get("/dashboard")
        assert_status(response, 200, "dashboard")

        response = client.post(
            "/generation/create",
            data={
                "source_type": "text",
                "source_content": "Tendências de IA para indústria em 2026",
            },
        )
        assert_status(response, 200, "generation")

        response = client.get("/dashboard/jobs/live")
        assert_status(response, 200, "jobs-live")
        payload = response.json()
        if "jobs" not in payload:
            raise RuntimeError("jobs-live failed: payload sem campo jobs")

        response = client.post("/logout")
        assert_status(response, 200, "logout")

    print("client-smoke-test:ok")


if __name__ == "__main__":
    main()
