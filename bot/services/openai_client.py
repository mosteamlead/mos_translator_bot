from openai import AsyncOpenAI

from bot.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)