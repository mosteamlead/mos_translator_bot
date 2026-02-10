from typing import Literal

from bot.config import settings
from bot.services.openai_client import client
from bot.services.lang_detect import detect_language

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
    Перевод между RU/EN/VI с пост‑проверкой языка ответа.
    Если модель вернула не целевой язык, принудительно
    перезапрашиваем перевод уже полученного текста.
    """
    source_name = LANG_NAMES[source_lang]
    target_name = LANG_NAMES[target_lang]

    system_prompt = (
        "You are a professional translator.\n"
        "Translate user text between languages without explanations.\n"
        "Return ONLY the translated text, no quotes, no commentary."
    )

    base_user_prompt = (
        f"Source language: {source_name}\n"
        f"Target language: {target_name}\n"
        "Instructions: Translate the text below from the source language "
        f"to the target language.\n\n"
        f"Text:\n{text}"
    )

    async def call_model(user_prompt: str) -> str:
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()

    # 1. Первый вызов
    translation = await call_model(base_user_prompt)

    # 2. Проверяем язык результата
    out_lang = detect_language(translation)
    if out_lang is not None and out_lang == target_lang:
        return translation

    # 3. Второй шанс: заставляем ещё раз перевести уже полученный текст
    retry_prompt = (
        f"Source language: {source_name}\n"
        f"Target language: {target_name}\n"
        "The previous attempt did not produce text in the target language.\n"
        "Now, translate the following text to the target language.\n"
        "Answer ONLY in the target language, without explanations "
        "or mixing languages.\n\n"
        f"Text:\n{translation}"
    )
    translation2 = await call_model(retry_prompt)
    return translation2.strip()