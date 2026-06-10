"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # App
    app_name: str = "Norani Portal API"
    environment: str = "production"
    debug: bool = False

    # Database
    database_url: str
    database_url_sync: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # AppKey encryption (Fernet key)
    appkey_encryption_key: str

    # ChirpStack
    chirpstack_api_url: str = "localhost:8080"
    chirpstack_api_token: str

    # InfluxDB
    influxdb_url: str = "http://localhost:8086"
    influxdb_token: str = ""
    influxdb_org: str = "norani"
    influxdb_bucket: str = "lorawan-data"

    # CORS — accepts comma-separated string from env, converts to list
    cors_origins: str = "http://localhost:5173"

    # Pricing
    default_price_per_device_rwf: int = 1500

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance. Called from dependency injection."""
    return Settings()
