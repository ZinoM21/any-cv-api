from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AnyCV API"

    port: int

    nextauth_url: str
    nextauth_secret: str

    mongodb_url: str

    rapidapi_url: str
    rapidapi_host: str
    rapidapi_key: str

    frontend_url: str

    supabase_url: str
    supabase_key: str
    supabase_bucket: str = "files"

    model_config = SettingsConfigDict(env_file=".env")

    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 60 * 24 * 7
    auth_algorithm: str = "HS256"
    public_paths: List[str] = [
        "/healthz",
        "/api/v1",
        "/api/v1/healthz",
        "/api/v1/profile/healthz",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh-access",
    ]


settings = Settings()  # type: ignore
