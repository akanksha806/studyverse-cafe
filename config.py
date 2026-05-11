# =============================================================
# config.py — Studyverse Café | App Configuration
# =============================================================
# All sensitive settings (DB password, email credentials) are
# loaded from environment variables via a .env file.
# NEVER hardcode real passwords here — use .env instead.
# =============================================================

import os
from dotenv import load_dotenv

# Loads variables from your .env file into os.environ
load_dotenv()


class Config:
    # ── Security ─────────────────────────────────────────────
    # Secret key used by Flask to sign session cookies.
    # Generate a strong one: python -c "import secrets; print(secrets.token_hex())"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

    # ── MySQL Database ────────────────────────────────────────
    # These values are read from your .env file.
    MYSQL_HOST     = os.getenv("MYSQL_HOST",     "localhost")
    MYSQL_PORT     = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER     = os.getenv("MYSQL_USER",     "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB       = os.getenv("MYSQL_DB",       "studyverse_db")

    # ── Email (Gmail SMTP) ────────────────────────────────────
    # Used to send confirmation emails to customers.
    # For Gmail: enable "App Passwords" in Google Account settings.
    MAIL_SERVER   = os.getenv("MAIL_SERVER",   "smtp.gmail.com")
    MAIL_PORT     = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")   # your Gmail address
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")   # your Gmail App Password
    MAIL_SENDER   = os.getenv("MAIL_USERNAME", "")   # same as username

    # ── Café Info (used in emails) ────────────────────────────
    CAFE_NAME    = "Studyverse Café"
    CAFE_ADDRESS = "C-42, Malviya Nagar, Jaipur, Rajasthan 302017"
    CAFE_PHONE   = "+91 98765 43210"
    CAFE_EMAIL   = "m.akanshagupta@gmail.com"
