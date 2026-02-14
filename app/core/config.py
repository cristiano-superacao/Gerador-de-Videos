from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Agentes IA Studio"
    app_env: str = "development"
    secret_key: str = "change-me-in-production"

    database_url: str = "sqlite:///./agentes_ia.db"

    openai_api_key: str = ""
    tavily_api_key: str = ""
    perplexity_api_key: str = ""
    shotstack_api_key: str = ""
    shotstack_owner_id: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
