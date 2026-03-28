from app.models.video import VideoJob
from tests.helpers import get_user, login, register


def test_dashboard_renders_empty_state_and_account_data(client):
    register(client, "dashboard@example.com", "senha123")
    login(client, "dashboard@example.com", "senha123")

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Painel de Produção" in response.text
    assert "dashboard@example.com" in response.text
    assert "Sem gerações ainda." in response.text
    assert "Gerar 3 roteiros e vídeos" in response.text
    assert (
        "Formatos comuns: mp4, mov, mkv, webm, mp3, wav, m4a ou aac."
        in response.text
    )
    assert (
        '<script id="dashboard_config" type="application/json">'
        in response.text
    )
    assert '"maxUploadBytes": 26214400' in response.text
    assert (
        '"allowedExtensions": ["mp4", "mov", "mkv", '
        '"webm", "mp3", "wav", "m4a", "aac"]'
        in response.text
    )
    assert '<tbody id="jobs_table_body">' in response.text
    assert '<script src="/static/dashboard.js"></script>' in response.text


def test_dashboard_embeds_initial_jobs_json(client, db_session):
    register(client, "dashboard.jobs@example.com", "senha123")
    login(client, "dashboard.jobs@example.com", "senha123")
    user = get_user(db_session, "dashboard.jobs@example.com")

    job = VideoJob(
        user_id=user.id,
        source_type="text",
        source_content="conteudo base",
        script_variant=2,
        status="simulado",
        provider="shotstack",
        render_id="mock-render-id",
        output_url="https://cdn.example.com/video.mp4",
    )
    db_session.add(job)
    db_session.commit()

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Vídeo de demonstração" in response.text
    assert "https://cdn.example.com/video.mp4" in response.text
    assert "Visualizar" in response.text
    assert "Baixar" in response.text


def test_dashboard_hides_suspended_demo_video_links(client, db_session):
    register(client, "dashboard.demo.blocked@example.com", "senha123")
    login(client, "dashboard.demo.blocked@example.com", "senha123")
    user = get_user(db_session, "dashboard.demo.blocked@example.com")

    job = VideoJob(
        user_id=user.id,
        source_type="text",
        source_content="conteudo demo",
        script_variant=1,
        status="simulado",
        provider="shotstack",
        render_id="mock-render-id",
        output_url=(
            "https://cdn.shotstack.io/au/v1/msgtwx8iw6/"
            "3b36b6b5-3d3e-4c5e-8e0e-9c8f6a0b5d3e.mp4"
        ),
    )
    db_session.add(job)
    db_session.commit()

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Modo demonstração" in response.text
    assert "3b36b6b5-3d3e-4c5e-8e0e-9c8f6a0b5d3e.mp4" not in response.text
    assert "Visualizar" not in response.text


def test_dashboard_jobs_live_updates_pending_render(
    client,
    db_session,
    monkeypatch,
):
    register(client, "polling@example.com", "senha123")
    login(client, "polling@example.com", "senha123")
    user = get_user(db_session, "polling@example.com")

    pending_job = VideoJob(
        user_id=user.id,
        source_type="text",
        source_content="conteudo base",
        script_variant=1,
        status="queued",
        provider="shotstack",
        render_id="render-123",
        output_url="",
    )
    db_session.add(pending_job)
    db_session.commit()

    async def fake_render_status(self, render_id: str):
        assert render_id == "render-123"
        return {
            "status": "done",
            "output_url": "https://cdn.example.com/video-final.mp4",
        }

    monkeypatch.setattr(
        "app.services.video_gen.VideoGenerator.get_render_status",
        fake_render_status,
    )

    response = client.get("/dashboard/jobs/live")
    db_session.refresh(pending_job)
    payload = response.json()

    assert response.status_code == 200
    assert "html" in payload
    assert payload["has_demo_mode"] is False
    assert payload["jobs"][0]["status"] == "done"
    assert (
        payload["jobs"][0]["output_url"]
        == "https://cdn.example.com/video-final.mp4"
    )
    assert "https://cdn.example.com/video-final.mp4" in payload["html"]
    assert pending_job.status == "done"


def test_dashboard_requires_authentication(client):
    response = client.get("/dashboard")

    assert response.status_code == 401
    assert response.json()["detail"] == "Não autenticado"


def test_jobs_live_requires_authentication(client):
    response = client.get("/dashboard/jobs/live")

    assert response.status_code == 401
    assert response.json()["detail"] == "Não autenticado"
