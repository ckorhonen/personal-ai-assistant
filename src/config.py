import os

"""Configuration constants for Telegram integration."""

USER_ID = os.getenv("CHAT_ID", "")
APP_DB_BACKEND = os.getenv("APP_DB_BACKEND", "sqlite")
