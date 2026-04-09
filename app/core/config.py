from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(
        default="Agentes IA Studio",
        validation_alias=AliasChoices("APP_NAME", "NOME_DO_APLICATIVO"),
    )
    app_env: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "AMBIENTE_APP"),
    )
    secret_key: str = Field(
        default="change-me-in-production",
        validation_alias=AliasChoices("SECRET_KEY", "CHAVE_SECRETA"),
    )

    database_url: str = Field(
        default="sqlite:///./agentes_ia.db",
        validation_alias=AliasChoices("DATABASE_URL", "URL_DO_BANCO_DE_DADOS"),
    )

    openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_API_KEY", "CHAVE_API_OPENAI"),
    )
    tavily_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("TAVILY_API_KEY", "CHAVE_API_TAVILY"),
    )
    perplexity_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "PERPLEXITY_API_KEY",
            "CHAVE_API_PERPLEXITY",
        ),
    )
    video_provider: str = Field(
        default="shotstack",
        validation_alias=AliasChoices(
            "VIDEO_PROVIDER",
            "PROVEDOR_DE_VIDEO",
        ),
    )
    shotstack_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "SHOTSTACK_API_KEY",
            "CHAVE_API_SHOTSTACK",
        ),
    )
    shotstack_owner_id: str = Field(
        default="",
        validation_alias=AliasChoices(
            "SHOTSTACK_OWNER_ID",
            "ID_DO_PROPRIETARIO_DO_SHOTSTACK",
            "ID_DO_PROPRIETÁRIO_DO_SHOTSTACK",
        ),
    )
    shotstack_env: str = Field(
        default="stage",
        validation_alias=AliasChoices(
            "SHOTSTACK_ENV",
            "AMBIENTE_SHOTSTACK",
        ),
    )
    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "GEMINI_API_KEY",
            "CHAVE_API_GEMINI",
        ),
    )
    veo_model: str = Field(
        default="veo-3.1-generate-preview",
        validation_alias=AliasChoices(
            "VEO_MODEL",
            "MODELO_VEO",
        ),
    )
    veo_aspect_ratio: str = Field(
        default="9:16",
        validation_alias=AliasChoices(
            "VEO_ASPECT_RATIO",
            "PROPORCAO_VEO",
        ),
    )
    veo_resolution: str = Field(
        default="720p",
        validation_alias=AliasChoices(
            "VEO_RESOLUTION",
            "RESOLUCAO_VEO",
        ),
    )
    veo_duration_seconds: int = Field(
        default=8,
        validation_alias=AliasChoices(
            "VEO_DURATION_SECONDS",
            "DURACAO_VEO_SEGUNDOS",
        ),
    )
    gemini_image_model: str = Field(
        default="gemini-3.1-flash-image-preview",
        validation_alias=AliasChoices(
            "GEMINI_IMAGE_MODEL",
            "MODELO_IMAGEM_GEMINI",
        ),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
