from typing import Set

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AnyCV API"
    PORT: int
    FRONTEND_URL: str
    MONGODB_URL: str

    # External Services
    RAPIDAPI_URL: str
    RAPIDAPI_HOST: str
    RAPIDAPI_KEY: str
    EXTERNAL_MAX_RETRIES: int = 4
    EXTERNAL_RETRY_DELAY_SECONDS: int = 1
    LINKEDIN_MEDIA_DOMAINS: Set[str] = {
        "media.licdn.com",
        "media-exp1.licdn.com",
        "media-exp2.licdn.com",
        "media-exp3.licdn.com",
    }

    # File Storage
    SUPABASE_URL: str
    SUPABASE_PUBLISHABLE_KEY: str
    SUPABASE_SECRET_KEY: str
    SUPABASE_PRIVATE_BUCKET: str = "files"
    SUPABASE_PUBLIC_BUCKET: str = "public-files"
    MAX_FILE_SIZE_MB: int = 5  # 5MB
    ALLOWED_MIME_TYPES: Set[str] = {
        "image/jpeg",
        "image/png",
        "image/gif",
    }
    SIGNED_FILE_EXPIRES_IN_SECONDS: int = 60

    # Cache
    CACHE_GUEST_PROFILES_TIME_IN_SECONDS: int = 60 * 60 * 24 * 7  # 1 week

    # Email
    RESEND_API_KEY: str
    RESEND_FROM_EMAIL: str
    RESEND_TO_EMAIL: str | None = None
    EMAIL_VERIFICATION_EXPIRES_IN_HOURS: int = 24

    # Auth
    AUTH_SECRET: str
    TURNSTILE_SECRET_KEY: str
    TURNSTILE_CHALLENGE_URL: str = (
        "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    )
    ACCESS_TOKEN_EXPIRES_IN_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRES_IN_MINUTES: int = 60 * 24 * 14  # 2 weeks
    AUTH_ALGORITHM: str = "HS256"
    PUBLIC_PATHS: list[str] = [
        "/healthz",
        "/docs",
        "/api/openapi.json",
        "/api/v1/healthz",
        "/api/v1/profile/",
        "/api/v1/auth/",
        "/api/v1/files/public/",
    ]  # We define them here as "public", but protected data is always secured through user authentication

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
