from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AnyCV API"

    port: int = 8000

    mongodb_url: str

    rapidapi_url: str
    rapidapi_host: str
    rapidapi_key: str

    frontend_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
