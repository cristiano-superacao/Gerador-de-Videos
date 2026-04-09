import scripts.seed as seed_module
from app.models.video import VideoJob
from tests.helpers import get_user, login, register


def test_public_pages_keep_responsive_layout_markers(client):
    home_response = client.get("/")
    how_to_use_response = client.get("/como-usar")

    assert home_response.status_code == 200
    assert how_to_use_response.status_code == 200
    assert "<meta name=\"viewport\"" in home_response.text
    assert "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" in home_response.text
    assert "grid lg:grid-cols-2 gap-8 items-center" in home_response.text
    assert "grid lg:grid-cols-2 gap-4 sm:gap-5" in how_to_use_response.text


def test_home_redirects_authenticated_user_to_dashboard(client):
    register(client, "redirect.home@example.com", "senha123")
    login(client, "redirect.home@example.com", "senha123")

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


def test_favicon_redirects_to_static_asset(client):
    response = client.get("/favicon.ico", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/favicon.svg"


def test_logout_redirects_to_home(client):
    register(client, "logout.flow@example.com", "senha123")
    login(client, "logout.flow@example.com", "senha123")

    response = client.post("/logout", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/"


def test_seed_jobs_cover_key_states(test_db_session_factory, monkeypatch):
    monkeypatch.setattr(seed_module, "SessionLocal", test_db_session_factory)
    user = seed_module.ensure_user(
        email="seed@example.com",
        password="senha123",
        credits=30,
        is_admin=False,
    )

    seed_module.reset_seed_jobs(user.id)
    seed_module.create_seed_jobs(user.id)

    session = test_db_session_factory()
    try:
        jobs = (
            session.query(VideoJob)
            .filter(VideoJob.user_id == user.id)
            .order_by(VideoJob.id.asc())
            .all()
        )
    finally:
        session.close()

    statuses = {job.status for job in jobs}
    assert len(jobs) == 6
    assert {"done", "fetching", "queued", "rendering", "simulado"} == statuses
    assert any(job.provider == "veo" for job in jobs)
    assert any(
        job.output_url == "https://cdn.example.com/seed-video.mp4"
        for job in jobs
    )


def test_seed_main_creates_demo_users_and_jobs(
    test_db_session_factory,
    monkeypatch,
):
    monkeypatch.setattr(seed_module, "SessionLocal", test_db_session_factory)
    monkeypatch.setattr(
        seed_module.Base.metadata,
        "create_all",
        lambda bind: None,
    )
    monkeypatch.setattr(seed_module, "engine", object())
    monkeypatch.setenv("SEED_APP_USER_EMAIL", "principal@example.com")
    monkeypatch.setenv("SEED_APP_USER_PASSWORD", "senha123")
    monkeypatch.setenv("SEED_REVIEWER_EMAIL", "reviewer@example.com")
    monkeypatch.setenv("SEED_REVIEWER_PASSWORD", "senha456")

    seed_module.main()

    session = test_db_session_factory()
    try:
        app_user = get_user(session, "principal@example.com")
        reviewer = get_user(session, "reviewer@example.com")
        admin = get_user(session, "admin@agentesia.com")
        app_jobs = (
            session.query(VideoJob)
            .filter(VideoJob.user_id == app_user.id)
            .all()
        )
    finally:
        session.close()

    assert (
        admin is not None
        and admin.is_admin is True
        and admin.credits == 999
    )
    assert app_user is not None and app_user.credits == 50
    assert reviewer is not None and reviewer.credits == 12
    assert len(app_jobs) == 6
