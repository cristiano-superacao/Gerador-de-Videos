from app.models.video import VideoJob
from tests.helpers import get_user, login, register


def test_generation_text_creates_three_jobs_and_consumes_credit(
    client,
    db_session,
):
    register(client, "geracao@example.com", "senha123")
    login(client, "geracao@example.com", "senha123")

    response = client.post(
        "/generation/create",
        data={
            "source_type": "text",
            "source_content": "Tendências de IA para PMEs em 2026",
        },
        follow_redirects=True,
    )

    user = get_user(db_session, "geracao@example.com")
    jobs = (
        db_session.query(VideoJob)
        .filter(VideoJob.user_id == user.id)
        .order_by(VideoJob.id.asc())
        .all()
    )

    assert response.status_code == 200
    assert "Resultado da Geração" in response.text
    assert "Vídeo 1" in response.text
    assert "Configure SHOTSTACK_API_KEY para render real." in response.text
    assert (
        "Os roteiros foram gerados, mas o vídeo externo não será "
        "publicado neste ambiente." in response.text
    )
    assert user.credits == 4
    assert len(jobs) == 3
    assert all(job.status == "simulado" for job in jobs)
    assert all(job.requested_provider == "shotstack" for job in jobs)
    assert all(job.status_message for job in jobs)


def test_generation_video_creates_jobs_from_upload(client, db_session):
    register(client, "video@example.com", "senha123")
    login(client, "video@example.com", "senha123")

    response = client.post(
        "/generation/create",
        data={"source_type": "video", "source_content": ""},
        files={
            "source_file": (
                "entrevista.mp3",
                b"audio-fake-content",
                "audio/mpeg",
            )
        },
        follow_redirects=True,
    )

    user = get_user(db_session, "video@example.com")
    jobs = db_session.query(VideoJob).filter_by(user_id=user.id).all()

    assert response.status_code == 200
    assert "Resultado da Geração" in response.text
    assert len(jobs) == 3
    assert all(job.source_type == "video" for job in jobs)
    assert all(job.source_content == "entrevista.mp3" for job in jobs)


def test_generation_requires_authentication(client):
    response = client.post(
        "/generation/create",
        data={
            "source_type": "text",
            "source_content": "Sem sessão autenticada",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Não autenticado"


def test_generation_blocks_when_user_has_no_credits(client, db_session):
    register(client, "semcredito@example.com", "senha123")
    login(client, "semcredito@example.com", "senha123")
    user = get_user(db_session, "semcredito@example.com")
    user.credits = 0
    db_session.commit()

    response = client.post(
        "/generation/create",
        data={
            "source_type": "text",
            "source_content": "Tema sem saldo",
        },
        follow_redirects=True,
    )

    db_session.refresh(user)
    jobs = db_session.query(VideoJob).filter_by(user_id=user.id).all()

    assert response.status_code == 400
    assert "Créditos insuficientes para gerar novos vídeos." in response.text
    assert user.credits == 0
    assert jobs == []


def test_generation_rejects_invalid_video_extension(client, db_session):
    register(client, "arquivoinvalido@example.com", "senha123")
    login(client, "arquivoinvalido@example.com", "senha123")
    user = get_user(db_session, "arquivoinvalido@example.com")

    response = client.post(
        "/generation/create",
        data={"source_type": "video", "source_content": ""},
        files={
            "source_file": (
                "documento.txt",
                b"conteudo-invalido",
                "text/plain",
            )
        },
        follow_redirects=True,
    )

    jobs = db_session.query(VideoJob).filter_by(user_id=user.id).all()

    assert response.status_code == 400
    assert "Formato não permitido." in response.text
    assert jobs == []


def test_generation_rejects_video_above_max_size(
    client,
    db_session,
    monkeypatch,
):
    register(client, "arquivogrande@example.com", "senha123")
    login(client, "arquivogrande@example.com", "senha123")
    user = get_user(db_session, "arquivogrande@example.com")
    monkeypatch.setattr(
        "app.routes.generation.MAX_UPLOAD_SIZE_BYTES",
        1024 * 1024,
    )

    response = client.post(
        "/generation/create",
        data={"source_type": "video", "source_content": ""},
        files={
            "source_file": (
                "podcast.mp3",
                b"0" * ((1024 * 1024) + 1),
                "audio/mpeg",
            )
        },
        follow_redirects=True,
    )

    jobs = db_session.query(VideoJob).filter_by(user_id=user.id).all()

    assert response.status_code == 400
    assert "Arquivo excede 1MB." in response.text
    assert jobs == []
