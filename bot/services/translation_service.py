from typing import Literal

from bot.config import settings
from bot.services.openai_client import client

AppLang = Literal["RU", "EN", "VI"]

LANG_NAMES = {
    "RU": "Russian",
    "EN": "English",
    "VI": "Vietnamese",
}


async def translate_text(
    text: str,
    source_lang: AppLang,
    target_lang: AppLang,
) -> str:
    """
    Translate text from source_lang to target_lang using GPT model.
    Returns translation as plain text.
    """
    source_name = LANG_NAMES[source_lang]
    target_name = LANG_NAMES[target_lang]

    system_prompt = (
        "You are a professional translator. "
        "Translate user text between languages without explanations. "
        "Return ONLY the translated text, no quotes, no commentary."
    )

    user_prompt = (
        f"Source language: {source_name}\n"
        f"Target language: {target_name}\n"
        f"Text:\n{text}"
    )

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return (response.choices[0].message.content or "").strip()