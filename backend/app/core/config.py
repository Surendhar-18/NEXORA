from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "NEXORA Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Storage paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    EVIDENCE_DIR: Path = DATA_DIR / "evidence"
    MODEL_DIR: Path = DATA_DIR / "models"
    VENUE_DIR: Path = DATA_DIR / "venue"

    # Database
    DATABASE_URL: str = ""

    def __init__(self, **values):
        super().__init__(**values)
        if not self.DATABASE_URL or self.DATABASE_URL == "sqlite:///./data/nexora.db":
            db_path = self.DATA_DIR / "nexora.db"
            # Normalize for Windows sqlite URL with 4 slashes or posix path
            self.DATABASE_URL = f"sqlite:///{db_path.as_posix()}"

    MAX_UPLOAD_SIZE_MB: float = 500

    # Security & Authentication
    JWT_SECRET_KEY: str = "nexora-production-hardened-hmac-sha256-secret-key-32bytes-min"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REQUIRE_AUTH: bool = False  # Set to True in production to strictly enforce JWT tokens
    RATE_LIMIT_LOGIN_MAX: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 60

settings = Settings()
