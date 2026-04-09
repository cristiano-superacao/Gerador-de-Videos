import pytest

import scripts.client_smoke_test as client_smoke_test
import scripts.system_validation as system_validation


class FakeResponse:
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data if json_data is not None else {}

    def json(self):
        return self._json_data


class FakeHttpxClient:
    def __init__(self, responses):
        self.responses = responses

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, path):
        return self.responses[("GET", path)]

    def post(self, path, data=None, files=None):
        return self.responses[("POST", path)]


def test_get_user_id_from_admin_page_reads_credit_form_action():
    html = """
    <table>
      <tr>
        <td>usuario@example.com</td>
        <td>
          <form action="/admin/users/42/credits" method="post"></form>
        </td>
      </tr>
    </table>
    """

    user_id = client_smoke_test.get_user_id_from_admin_page(
        html,
        "usuario@example.com",
    )

    assert user_id == 42


def test_ensure_user_session_registers_when_login_fails():
    class FakeClient:
        def __init__(self):
            self.calls = []
            self._login_attempts = 0

        def post(self, path, data=None):
            self.calls.append((path, data))
            if path == "/login":
                self._login_attempts += 1
                if self._login_attempts == 1:
                    return FakeResponse(status_code=401)
                return FakeResponse(status_code=200)
            if path == "/register":
                return FakeResponse(status_code=200)
            raise AssertionError(f"unexpected path: {path}")

    client = FakeClient()

    client_smoke_test.ensure_user_session(
        client,
        "novo@example.com",
        "senha123",
    )

    assert [call[0] for call in client.calls] == [
        "/login",
        "/register",
        "/login",
    ]


def test_validate_pages_and_apis_accepts_operational_job_fields(monkeypatch):
    html_home = """
    <html>
            <head>
                <meta name="viewport"
                            content="width=device-width, initial-scale=1" />
            </head>
      <body>
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"></div>
        <div class="grid lg:grid-cols-2 gap-8 items-center"></div>
      </body>
    </html>
    """
    html_how_to = """
        <html>
            <body>
                <div class="grid lg:grid-cols-2 gap-4 sm:gap-5"></div>
            </body>
        </html>
    """

    responses = {
        ("GET", "/"): FakeResponse(status_code=200, text=html_home),
        ("GET", "/como-usar"): FakeResponse(status_code=200, text=html_how_to),
        ("GET", "/login"): FakeResponse(status_code=200, text="login"),
        ("GET", "/register"): FakeResponse(status_code=200, text="register"),
        ("GET", "/dashboard"): FakeResponse(status_code=200, text="dashboard"),
        (
            "GET",
            "/dashboard/jobs/live",
        ): FakeResponse(
            status_code=200,
            json_data={
                "jobs": [
                    {
                        "provider": "shotstack",
                        "requested_provider": "veo",
                        "status_message": "fallback executado",
                    }
                ]
            },
        ),
        ("POST", "/register"): FakeResponse(status_code=200),
        ("POST", "/login"): FakeResponse(status_code=200),
        ("POST", "/generation/create"): FakeResponse(status_code=200),
    }

    monkeypatch.setattr(
        system_validation.httpx,
        "Client",
        lambda **kwargs: FakeHttpxClient(responses),
    )

    failures = system_validation.validate_pages_and_apis()

    assert failures == []


def test_client_smoke_main_fails_when_operational_fields_are_missing(
    monkeypatch,
):
    admin_html = """
    <table>
      <tr>
        <td>cristiano.s.santos@ba.estudante.senai.br</td>
        <td>
          <form action="/admin/users/7/credits" method="post"></form>
        </td>
      </tr>
    </table>
    """

    responses = {
        ("GET", "/"): FakeResponse(status_code=200, text="home"),
        ("GET", "/como-usar"): FakeResponse(status_code=200, text="how"),
        ("GET", "/dashboard"): FakeResponse(status_code=200, text="dashboard"),
        ("GET", "/dashboard/jobs/live"): FakeResponse(
            status_code=200,
            json_data={"jobs": [{"provider": "shotstack"}]},
        ),
        ("GET", "/admin/users"): FakeResponse(
            status_code=200,
            text=admin_html,
        ),
        ("POST", "/login"): FakeResponse(status_code=200),
        ("POST", "/generation/create"): FakeResponse(status_code=200),
        ("POST", "/logout"): FakeResponse(status_code=200),
        ("POST", "/admin/users/7/credits"): FakeResponse(status_code=200),
    }

    monkeypatch.setattr(
        client_smoke_test.httpx,
        "Client",
        lambda **kwargs: FakeHttpxClient(responses),
    )

    with pytest.raises(RuntimeError, match="campos ausentes no payload"):
        client_smoke_test.main()
