import logging
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from aiogram import Router, F
from aiogram.types import Message

from bot.db.storage import get_user_languages
from bot.services.lang_detect import detect_language
from bot.services.translation_service import translate_text, AppLang
from bot.services.voice_service import transcribe_audio
from bot.handlers.start import build_main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


def choose_direction(
    detected: Optional[str],
    lang_from: AppLang,
    lang_to: AppLang,
) -> Tuple[AppLang, AppLang]:
    """
    - If detected == lang_from -> translate to lang_to
    - If detected == lang_to   -> translate to lang_from
    - Else                     -> to lang_from
    """
    if detected == lang_from:
        return lang_from, lang_to
    if detected == lang_to:
        return lang_to, lang_from
    return detected or lang_from, lang_from


async def _ensure_lang_pair(message: Message) -> Optional[Tuple[AppLang, AppLang]]:
    user_id = message.from_user.id
    lang_pair = await get_user_languages(user_id)

    if not lang_pair or not lang_pair[0] or not lang_pair[1]:
        await message.answer(
            "Language pair is not configured yet.\n"
            "Please send /start and select two languages first."
        )
        return None

    lang_from, lang_to = lang_pair
    return lang_from, lang_to  # type: ignore[return-value]


@router.message(F.text & ~F.via_bot)
async def handle_text(message: Message):
    """
    Handle text messages: auto-detect language, choose direction, translate.
    """
    lang_pair = await _ensure_lang_pair(message)
    if not lang_pair:
        return

    lang_from, lang_to = lang_pair
    text = message.text.strip()

    detected = detect_language(text)
    logger.info(
        "Text message from %s, detected_lang=%s, pair=(%s,%s)",
        message.from_user.id,
        detected,
        lang_from,
        lang_to,
    )

    src_lang, dst_lang = choose_direction(detected, lang_from, lang_to)
    try:
        translation = await translate_text(text, source_lang=src_lang, target_lang=dst_lang)
    except Exception as e:
        logger.exception("Translation error: %s", e)
        await message.answer("❌ Error while translating text. Please try again later.")
        return

    await message.answer(
        f"{translation}\n\n"
        "Если хочешь сменить языки — нажми одну из кнопок ниже 👇",
        reply_markup=build_main_menu_keyboard(),
    )


@router.message(F.voice | F.audio)
async def handle_voice(message: Message):
    """
    Handle voice messages:
    1. Download file
    2. Transcribe with Whisper
    3. Auto-detect language and translate
    """
    lang_pair = await _ensure_lang_pair(message)
    if not lang_pair:
        return

    lang_from, lang_to = lang_pair

    tmp_dir = Path(tempfile.gettempdir())
    file_name = f"tg_{message.from_user.id}_{message.message_id}.ogg"
    local_path = tmp_dir / file_name

    try:
        if message.voice:
            await message.bot.download(message.voice, destination=local_path)
        elif message.audio:
            await message.bot.download(message.audio, destination=local_path)
        else:
            await message.answer("Unsupported audio type.")
            return
    except Exception as e:
        logger.exception("Failed to download audio: %s", e)
        await message.answer("❌ Could not download audio file.")
        return

    try:
        text = await transcribe_audio(local_path)
    except Exception as e:
        logger.exception("Failed to transcribe audio: %s", e)
        await message.answer("❌ Error while transcribing your voice message.")
        return
    finally:
        try:
            if local_path.exists():
                local_path.unlink()
        except OSError:
            pass

    if not text.strip():
        await message.answer("I could not recognize any speech in this audio.")
        return

    detected = detect_language(text)
    logger.info(
        "Voice message from %s, detected_lang=%s, pair=(%s,%s)",
        message.from_user.id,
        detected,
        lang_from,
        lang_to,
    )

    src_lang, dst_lang = choose_direction(detected, lang_from, lang_to)
    try:
        translation = await translate_text(text, source_lang=src_lang, target_lang=dst_lang)
    except Exception as e:
        logger.exception("Translation error (voice): %s", e)
        await message.answer("❌ Error while translating your voice message.")
        return

    await message.answer(
        f"🗣 <b>Recognized text:</b>\n{text}\n\n"
        f"🌐 <b>Translation:</b>\n{translation}\n\n"
        "Если хочешь сменить языки — нажми одну из кнопок ниже 👇",
        reply_markup=build_main_menu_keyboard(),
    )