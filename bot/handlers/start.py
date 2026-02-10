from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db.storage import set_lang_from, set_lang_to, get_user_languages, reset_user_languages

router = Router()

LANGS = {
    "RU": {"flag": "🇷🇺", "label": "Russian"},
    "EN": {"flag": "🇬🇧", "label": "English"},
    "VI": {"flag": "🇻🇳", "label": "Vietnamese"},
}


def build_first_lang_keyboard():
    builder = InlineKeyboardBuilder()
    for code, meta in LANGS.items():
        text = f"{meta['flag']} {meta['label']} ({code})"
        builder.button(text=text, callback_data=f"lang1:{code}")
    builder.adjust(3)
    return builder.as_markup()


def build_second_lang_keyboard(exclude_code: str):
    builder = InlineKeyboardBuilder()
    for code, meta in LANGS.items():
        if code == exclude_code:
            continue
        text = f"{meta['flag']} {meta['label']} ({code})"
        builder.button(text=text, callback_data=f"lang2:{code}")
    builder.adjust(2)
    return builder.as_markup()


def build_main_menu_keyboard():
    """Инлайн-меню с кнопкой 'выбрать другие языки'."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔁 Выбрать другие языки",
        callback_data="change_lang",
    )
    builder.adjust(1)
    return builder.as_markup()


async def _ask_first_language(message: Message):
    await message.answer(
        "Hi! I am a bilingual translator bot.\n\n"
        "First, choose your **first language**:",
        reply_markup=build_first_lang_keyboard(),
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Старт / перезапуск выбора языков."""
    await reset_user_languages(message.from_user.id)
    await _ask_first_language(message)


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """
    Простое меню с кнопкой 'выбрать другие языки'.
    """
    await message.answer(
        "Меню:\n"
        "— Нажми кнопку ниже, чтобы выбрать другую пару языков.",
        reply_markup=build_main_menu_keyboard(),
    )


@router.callback_query(F.data == "change_lang")
async def on_change_lang(callback: CallbackQuery):
    """
    Обработка кнопки 'выбрать другие языки' из меню.
    """
    user_id = callback.from_user.id
    await reset_user_languages(user_id)

    await callback.message.edit_text(
        "Ок, давай выберем языки заново.\n\n"
        "Сначала выбери **первый язык**:",
        reply_markup=build_first_lang_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang1:"))
async def on_first_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split(":", maxsplit=1)[1]

    await set_lang_from(user_id, lang_from=lang_code)

    meta = LANGS[lang_code]
    await callback.message.edit_text(
        f"First language set to {meta['flag']} {meta['label']} ({lang_code}).\n\n"
        "Now, choose your **second language**:",
        reply_markup=build_second_lang_keyboard(exclude_code=lang_code),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang2:"))
async def on_second_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang_to_code = callback.data.split(":", maxsplit=1)[1]

    await set_lang_to(user_id, lang_to=lang_to_code)
    lang_from_code, _ = await get_user_languages(user_id)

    if not lang_from_code:
        await callback.message.edit_text(
            "Something went wrong. Please send /start to configure languages again."
        )
        await callback.answer()
        return

    from_meta = LANGS[lang_from_code]
    to_meta = LANGS[lang_to_code]

    await callback.message.edit_text(
        "Language pair configured ✅\n\n"
        f"• From: {from_meta['flag']} {from_meta['label']} ({lang_from_code})\n"
        f"• To: {to_meta['flag']} {to_meta['label']} ({lang_to_code})\n\n"
        "Now send me any text or voice message.\n"
        "- If you write in the first language, I'll translate to the second.\n"
        "- If you write in the second, I'll translate to the first.\n"
        "- Other languages → I translate to the first language.\n\n"
        "Если хочешь сменить пару — используй /menu или кнопку ниже.",
        reply_markup=build_main_menu_keyboard(),
    )
    await callback.answer()