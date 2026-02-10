from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db.storage import (
    set_lang_from,
    set_lang_to,
    get_user_languages,
)

router = Router()

# Фиксируем, что родной язык всегда русский
NATIVE_LANG = "RU"

LANGS = {
    "RU": {"flag": "🇷🇺", "label": "Russian"},
    "EN": {"flag": "🇬🇧", "label": "English"},
    "VI": {"flag": "🇻🇳", "label": "Vietnamese"},
}


def build_target_lang_keyboard():
    """
    Клавиатура выбора языка перевода.
    Русский зашит как родной, поэтому даём только EN и VI.
    """
    builder = InlineKeyboardBuilder()
    for code in ("EN", "VI"):
        meta = LANGS[code]
        text = f"{meta['flag']} {meta['label']} ({code})"
        builder.button(text=text, callback_data=f"to:{code}")
    builder.adjust(2)
    return builder.as_markup()


async def _ask_target_language(message: Message, with_greeting: bool = True):
    """
    Показать пользователю выбор языка перевода.
    """
    if with_greeting:
        prefix = (
            "Привет! Я бот‑переводчик.\n\n"
            "Русский язык уже выбран как родной.\n"
        )
    else:
        prefix = ""

    await message.answer(
        prefix + "Выбери язык, на который переводить сообщения:",
        reply_markup=build_target_lang_keyboard(),
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    /start — начать с нуля, выбрать язык перевода.
    Родной язык всегда русский.
    """
    # Зашиваем русским как родной
    await set_lang_from(message.from_user.id, lang_from=NATIVE_LANG)
    await _ask_target_language(message, with_greeting=True)


@router.message(Command("lang"))
async def cmd_lang(message: Message):
    """
    /lang — сменить язык перевода, не меняя того, что родной язык русский.
    """
    await set_lang_from(message.from_user.id, lang_from=NATIVE_LANG)
    await _ask_target_language(message, with_greeting=False)


@router.callback_query(F.data.startswith("to:"))
async def on_target_language(callback: CallbackQuery):
    """
    Обработка выбора языка перевода (EN или VI).
    """
    user_id = callback.from_user.id
    lang_to_code = callback.data.split(":", maxsplit=1)[1]

    # Сохраняем пару RU -> lang_to_code
    await set_lang_from(user_id, lang_from=NATIVE_LANG)
    await set_lang_to(user_id, lang_to=lang_to_code)

    lang_from_code, _ = await get_user_languages(user_id)
    from_meta = LANGS[lang_from_code]
    to_meta = LANGS[lang_to_code]

    await callback.message.edit_text(
        f"Язык перевода настроен ✅\n\n"
        f"{from_meta['flag']} Русский (RU) → "
        f"{to_meta['flag']} {to_meta['label']} ({lang_to_code})\n\n"
        "Теперь можешь отправлять мне текст или голосовые.\n"
        "- Если говоришь или пишешь по‑русски, переведу на выбранный язык.\n"
        "- Если пишешь на выбранном языке, переведу на русский.",
    )
    await callback.answer()