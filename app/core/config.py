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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
