from typing import List, Set

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AnyCV API"
    port: int
    frontend_url: str
    mongodb_url: str

    # External Services
    rapidapi_url: str
    rapidapi_host: str
    rapidapi_key: str
    MAX_RETRIES: int = 4
    RETRY_DELAY_SECONDS: int = 1
    LINKEDIN_MEDIA_DOMAINS: Set[str] = {
        "media.licdn.com",
        "media-exp1.licdn.com",
        "media-exp2.licdn.com",
        "media-exp3.licdn.com",
    }

    # File Storage
    supabase_url: str
    supabase_publishable_key: str
    supabase_secret_key: str
    supabase_bucket: str = "files"
    MAX_FILE_SIZE_MB: int = 5  # 5MB
    ALLOWED_MIME_TYPES: Set[str] = {
        "image/jpeg",
        "image/png",
        "image/gif",
    }
    EXPIRES_IN_SECONDS: int = 60

    # Auth
    auth_secret: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 60 * 24 * 7
    auth_algorithm: str = "HS256"
    public_paths: List[str] = [
        "/healthz",
        "/api/v1/healthz",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh-access",
    ]
    optional_auth_paths: List[str] = [
        "/api/v1/profile/",
    ]

    @property
    def all_public_paths(self) -> List[str]:
        """All paths that shouldn't return 401 if no auth token is provided"""
        return self.public_paths + self.optional_auth_paths

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
