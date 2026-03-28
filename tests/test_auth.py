from tests.helpers import get_user, login, register


def test_auth_pages_use_shared_template(client):
    login_response = client.get("/login")
    register_response = client.get("/register")

    assert login_response.status_code == 200
    assert register_response.status_code == 200
    assert "Acessar painel" in login_response.text
    assert "Criar conta" in register_response.text
    assert "Use pelo menos 6 caracteres na senha." in register_response.text


def test_register_and_login_flow(client, db_session):
    response = register(client, "novo.usuario@example.com", "senha123")

    assert response.status_code == 302
    assert response.headers["location"] == "/login"

    user = get_user(db_session, "novo.usuario@example.com")
    assert user is not None
    assert user.credits == 5
    assert user.is_admin is False

    login_response = login(client, "novo.usuario@example.com", "senha123")

    assert login_response.status_code == 200
    assert "Painel de Produção" in login_response.text


def test_register_duplicate_email_returns_error(client):
    first_response = register(client, "duplicado@example.com", "senha123")
    second_response = client.post(
        "/register",
        data={"email": "duplicado@example.com", "password": "senha123"},
        follow_redirects=True,
    )

    assert first_response.status_code == 302
    assert second_response.status_code == 400
    assert "E-mail já cadastrado" in second_response.text
