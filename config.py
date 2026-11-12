"""App settings. Values come from environment variables (see .env.example)."""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    # Signs the session cookie. Set a long random value in .env for real use.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

    # The database file lives next to this file, so it does not matter which
    # folder you start Flask from.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True   # JavaScript cannot read the cookie
    SESSION_COOKIE_SAMESITE = "Lax"  # not sent on cross-site POSTs
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
