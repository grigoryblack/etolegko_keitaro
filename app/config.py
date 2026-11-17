from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    keitaro_api_url: str = "http://localhost/admin_api/v1"
    keitaro_api_key: str = ""
    database_url: str = "sqlite:///./app.db"

    google_redirect_url: str = "https://www.google.com"


settings = Settings()
