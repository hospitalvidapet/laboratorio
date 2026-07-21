import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

def normalize_url(url):
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-this-key")
    SQLALCHEMY_DATABASE_URI = normalize_url(
        os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR/'vidapet_dev.db'}")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    AUTO_SYNC_ENABLED = os.getenv("AUTO_SYNC_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    AUTO_SYNC_ON_STARTUP = os.getenv("AUTO_SYNC_ON_STARTUP", "true").lower() in {"1", "true", "yes", "on"}
    AUTO_SYNC_INTERVAL_MINUTES = int(os.getenv("AUTO_SYNC_INTERVAL_MINUTES", "30"))
