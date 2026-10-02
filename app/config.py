from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    environment: str
    dev_restaurant_id: int | None = None
    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = 480


settings = Settings()
