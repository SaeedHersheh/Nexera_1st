from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Address Intelligence Engine"
    app_env: str = "development"
    database_url: str = (
        "postgresql+psycopg://address_user:address_password"
        "@localhost:5432/address_intelligence"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
