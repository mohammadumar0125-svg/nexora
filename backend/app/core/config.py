import os
from typing import List


def _normalize_db_url(url: str) -> str:
    """Force the psycopg2 driver and accept postgres:// style URLs (Render, Neon, Heroku)."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


class Settings:
    PROJECT_NAME: str = "NEXORA Business Operating System"
    VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api"
    APP_ENV: str = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower()

    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "nexora_enterprise")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "nexora_owner")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "nexora_owner_secret")
    DB_API_USER: str = os.getenv("DB_API_USER", "api_role")
    DB_API_PASSWORD: str = os.getenv("DB_API_PASSWORD", "api_secret_pass")

    @property
    def DATABASE_URL(self) -> str:
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return _normalize_db_url(env_url)
        # Hosted deploys (Render/Neon/...) only provide the owner URL. Derive the
        # least-privilege api_role URL from it so row-level security stays enforced.
        owner_url = os.getenv("MIGRATION_DATABASE_URL")
        if owner_url:
            from sqlalchemy.engine import make_url

            return make_url(_normalize_db_url(owner_url)).set(
                username=self.DB_API_USER, password=self.DB_API_PASSWORD
            ).render_as_string(hide_password=False)
        return (
            f"postgresql+psycopg2://{self.DB_API_USER}:{self.DB_API_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def MIGRATION_DATABASE_URL(self) -> str:
        env_url = os.getenv("MIGRATION_DATABASE_URL")
        if env_url:
            return _normalize_db_url(env_url)
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "").lower() == "true" or (
        os.getenv("APP_ENV", "development").lower() in ("staging", "production")
    )
    CORS_ORIGINS: List[str] = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:3000,http://localhost:3000",
        ).split(",")
        if o.strip()
    ]

    SESSION_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    SEED_SAMPLE_WORKSPACE: bool = os.getenv("SEED_SAMPLE_WORKSPACE", "true").lower() == "true"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")

    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local").lower()
    LOCAL_UPLOAD_DIR: str = os.getenv(
        "LOCAL_UPLOAD_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "private_uploads")),
    )
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "")
    MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))


settings = Settings()
