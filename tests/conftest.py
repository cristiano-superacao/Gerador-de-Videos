import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.core.database as database_module  # noqa: E402
import app.main as app_main  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402


@pytest.fixture(autouse=True)
def reset_runtime_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "video_provider", "shotstack")
    monkeypatch.setattr(settings, "shotstack_api_key", "")
    monkeypatch.setattr(settings, "shotstack_owner_id", "")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(
        settings,
        "gemini_image_model",
        "gemini-3.1-flash-image-preview",
    )
    monkeypatch.setattr(
        settings,
        "veo_model",
        "veo-3.1-generate-preview",
    )
    monkeypatch.setattr(settings, "veo_aspect_ratio", "9:16")
    monkeypatch.setattr(settings, "veo_resolution", "720p")
    monkeypatch.setattr(settings, "veo_duration_seconds", 8)


@pytest.fixture()
def test_db_session_factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_path = tmp_path / "test_app.db"
    test_engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    monkeypatch.setattr(database_module, "engine", test_engine)
    monkeypatch.setattr(database_module, "SessionLocal", testing_session_local)
    monkeypatch.setattr(app_main, "engine", test_engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app_main.app.dependency_overrides[database_module.get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)

    try:
        yield testing_session_local
    finally:
        app_main.app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture()
def client(test_db_session_factory):
    with TestClient(app_main.app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(test_db_session_factory):
    session = test_db_session_factory()
    try:
        yield session
    finally:
        session.close()
