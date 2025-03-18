from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AnyCV API"

    port: int

    mongodb_url: str

    rapidapi_url: str
    rapidapi_host: str
    rapidapi_key: str

    frontend_url: str

    supabase_url: str
    supabase_key: str
    supabase_bucket: str = "files"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
