from tests.helpers import get_user, login, register


def test_admin_can_update_user_credits(client, db_session):
    register(client, "cliente@example.com", "senha123")
    customer = get_user(db_session, "cliente@example.com")

    admin_login = login(client, "admin@agentesia.com", "admin123")
    assert admin_login.status_code == 200

    response = client.post(
        f"/admin/users/{customer.id}/credits",
        data={"credits": 42},
        follow_redirects=True,
    )

    db_session.refresh(customer)

    assert response.status_code == 200
    assert customer.credits == 42
    assert "Administração de Usuários" in response.text
    assert "cliente@example.com" in response.text


def test_admin_update_nonexistent_user_keeps_page_stable(client):
    login(client, "admin@agentesia.com", "admin123")

    response = client.post(
        "/admin/users/999999/credits",
        data={"credits": 88},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Administração de Usuários" in response.text


def test_admin_routes_forbid_standard_user(client):
    register(client, "padrao@example.com", "senha123")
    login(client, "padrao@example.com", "senha123")

    response = client.get("/admin/users")

    assert response.status_code == 403
    assert response.json()["detail"] == "Acesso restrito"
