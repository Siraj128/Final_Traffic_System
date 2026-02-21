import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_for_dev_only")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    FERNET_KEY = os.getenv("FERNET_KEY")

    # SMTP Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

    # Database
    SQLITE_URL = os.getenv("SQLITE_URL", "sqlite:///../Database/reward_app.db")

    # Google Auth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

    # Internal
    INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "fallback_dev_key")
