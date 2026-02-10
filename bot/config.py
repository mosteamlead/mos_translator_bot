import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_whisper_model: str = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")
    database_path: str = os.getenv("DATABASE_PATH", "bot.db")


settings = Settings()

if not settings.telegram_bot_token:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment / .env")

if not settings.openai_api_key:
    raise RuntimeError("OPENAI_API_KEY is not set in environment / .env")