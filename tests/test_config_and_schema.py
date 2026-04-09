from sqlalchemy import inspect

from app.core.config import Settings
from app.core.database import normalize_database_url


def test_settings_support_portuguese_aliases():
    settings = Settings(
        NOME_DO_APLICATIVO="Studio Teste",
        AMBIENTE_APP="production",
        CHAVE_SECRETA="segredo",
        URL_DO_BANCO_DE_DADOS="sqlite:///./teste.db",
        CHAVE_API_OPENAI="openai-key",
        CHAVE_API_TAVILY="tavily-key",
        CHAVE_API_PERPLEXITY="perplexity-key",
        PROVEDOR_DE_VIDEO="veo",
        CHAVE_API_SHOTSTACK="shotstack-key",
        ID_DO_PROPRIETARIO_DO_SHOTSTACK="owner-id",
        AMBIENTE_SHOTSTACK="production",
        CHAVE_API_GEMINI="gemini-key",
        MODELO_VEO="veo-3.1-lite-generate-preview",
        PROPORCAO_VEO="9:16",
        RESOLUCAO_VEO="720p",
        DURACAO_VEO_SEGUNDOS=8,
        MODELO_IMAGEM_GEMINI="gemini-3.1-flash-image-preview",
    )

    assert settings.app_name == "Studio Teste"
    assert settings.app_env == "production"
    assert settings.secret_key == "segredo"
    assert settings.database_url == "sqlite:///./teste.db"
    assert settings.openai_api_key == "openai-key"
    assert settings.tavily_api_key == "tavily-key"
    assert settings.perplexity_api_key == "perplexity-key"
    assert settings.video_provider == "veo"
    assert settings.shotstack_api_key == "shotstack-key"
    assert settings.shotstack_owner_id == "owner-id"
    assert settings.shotstack_env == "production"
    assert settings.gemini_api_key == "gemini-key"
    assert settings.veo_model == "veo-3.1-lite-generate-preview"
    assert settings.veo_aspect_ratio == "9:16"
    assert settings.veo_resolution == "720p"
    assert settings.veo_duration_seconds == 8
    assert settings.gemini_image_model == "gemini-3.1-flash-image-preview"


def test_normalize_database_url_adds_sslmode_for_postgres():
    result = normalize_database_url(
        "postgresql://user:pass@db.example.com:5432/app"
    )

    assert "sslmode=require" in result


def test_normalize_database_url_keeps_existing_sslmode():
    result = normalize_database_url(
        "postgresql://user:pass@db.example.com:5432/app?sslmode=disable"
    )

    assert result.endswith("sslmode=disable")


def test_test_database_contains_expected_tables(client, db_session):
    inspector = inspect(db_session.bind)
    tables = set(inspector.get_table_names())

    assert {"users", "video_jobs"}.issubset(tables)

    video_job_columns = {
        column["name"] for column in inspector.get_columns("video_jobs")
    }
    assert "render_id" in video_job_columns
    assert "output_url" in video_job_columns
    assert "requested_provider" in video_job_columns
    assert "status_message" in video_job_columns
