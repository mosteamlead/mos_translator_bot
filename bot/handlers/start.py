from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db.storage import (
    set_lang_from,
    set_lang_to,
    get_user_languages,
    reset_user_languages,
)

router = Router()

LANGS = {
    "RU": {"flag": "🇷🇺", "label": "Russian"},
    "EN": {"flag": "🇬🇧", "label": "English"},
    "VI": {"flag": "🇻🇳", "label": "Vietnamese"},
}

# Простейшая локализация текстов под родной язык
UI_TEXTS = {
    "EN": {
        "ask_first": (
            "Hi! I am a bilingual translator bot.\n\n"
            "First, choose your <b>native language</b>:"
        ),
        "ask_second": "Now choose your <b>second language</b>:",
        "pair_configured": (
            "Language pair configured ✅\n\n"
            "Now send me any text or voice message.\n"
            "- If you write in the first language, I'll translate to the second.\n"
            "- If you write in the second, I'll translate to the first.\n"
            "- Other languages → I translate to the first language.\n\n"
            "If you want to change languages, use /menu or the buttons below."
        ),
        "menu_title": (
            "Menu:\n"
            "— Use the buttons to change your language pair or native language."
        ),
        "change_lang_start": (
            "Okay, let's choose languages again.\n\n"
            "First, select your **native language**:"
        ),
    },
    "RU": {
        "ask_first": (
            "Привет! Я двуязычный бот‑переводчик.\n\n"
            "Сначала выбери свой <b>родной язык</b>:"
        ),
        "ask_second": "Теперь выбери <b>второй язык</b>:",
        "pair_configured": (
            "Пара языков настроена ✅\n\n"
            "Теперь можешь отправлять мне текст или голосовые.\n"
            "- Если пишешь на первом языке, переведу на второй.\n"
            "- Если пишешь на втором, переведу на первый.\n\n"
            "Если захочешь поменять — используй /menu или кнопки ниже."
        ),
        "menu_title": (
            "Меню:\n"
            "— Используй кнопки ниже, чтобы выбрать другую пару языков\n"
            "  или сменить родной язык."
        ),
        "change_lang_start": (
            "Хорошо, давай выберем языки заново.\n\n"
            "Сначала выбери свой <b>родной язык</b>:"
        ),
    },
    "VI": {
        "ask_first": (
            "Xin chào! Tôi là bot dịch song ngữ.\n\n"
            "Trước hết hãy chọn <b>ngôn ngữ mẹ đẻ</b> của bạn:"
        ),
        "ask_second": "Bây giờ hãy chọn <b>ngôn ngữ thứ hai</b>:",
        "pair_configured": (
            "Cặp ngôn ngữ đã được thiết lập ✅\n\n"
            "Bây giờ hãy gửi cho tôi bất kỳ văn bản hoặc tin nhắn thoại nào.\n"
            "- Nếu bạn viết bằng ngôn ngữ thứ nhất, tôi sẽ dịch sang ngôn ngữ thứ hai.\n"
            "- Nếu bạn viết bằng ngôn ngữ thứ hai, tôi sẽ dịch sang ngôn ngữ thứ nhất.\n"
            "- Ngôn ngữ khác → tôi dịch sang ngôn ngữ thứ nhất.\n\n"
            "Nếu muốn thay đổi – hãy dùng /menu hoặc các nút bên dưới."
        ),
        "menu_title": (
            "Menu:\n"
            "— Dùng các nút bên dưới để chọn lại cặp ngôn ngữ\n"
            "  hoặc thay đổi ngôn ngữ mẹ đẻ."
        ),
        "change_lang_start": (
            "Được, hãy chọn lại ngôn ngữ.\n\n"
            "Trước hết hãy chọn <b>ngôn ngữ mẹ đẻ</b>:"
        ),
    },
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


async def _ask_first_language(message: Message):
    await message.answer(
        "Hi! I am a bilingual translator bot.\n\n"
        "First, choose your <b>native language</b>:",
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
    Простое текстовое меню без кнопок.
    Пользователь управляет ботом только командами.
    """
    langs = await get_user_languages(message.from_user.id)
    native = langs[0] if langs and langs[0] else "RU"
    texts = UI_TEXTS.get(native, UI_TEXTS["EN"])

    await message.answer(
        texts["menu_title"]
        + "\n\nДоступные команды:\n"
        "- /start — выбрать языки заново\n"
        "- /menu — показать это меню",
    )


@router.callback_query(F.data.startswith("lang1:"))
async def on_first_language(callback: CallbackQuery):
    """
    Обработка выбора первого (родного) языка.
    """
    user_id = callback.from_user.id
    lang_code = callback.data.split(":", maxsplit=1)[1]

    await set_lang_from(user_id, lang_from=lang_code)

    meta = LANGS[lang_code]
    texts = UI_TEXTS.get(lang_code, UI_TEXTS["EN"])

    await callback.message.edit_text(
        f"{meta['flag']} {meta['label']} ({lang_code}) выбран как родной язык.\n\n"
        f"{texts['ask_second']}",
        reply_markup=build_second_lang_keyboard(exclude_code=lang_code),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang2:"))
async def on_second_language(callback: CallbackQuery):
    """
    Обработка выбора второго языка и переход в режим перевода.
    Сообщение показываем на родном языке.
    """
    user_id = callback.from_user.id
    lang_to_code = callback.data.split(":", maxsplit=1)[1]

    await set_lang_to(user_id, lang_to=lang_to_code)
    lang_from_code, _ = await get_user_languages(user_id)

    if not lang_from_code:
        await callback.message.edit_text(
            "Что-то пошло не так. Отправь /start и выбери языки заново."
        )
        await callback.answer()
        return

    from_meta = LANGS[lang_from_code]
    to_meta = LANGS[lang_to_code]

    texts = UI_TEXTS.get(lang_from_code, UI_TEXTS["EN"])

    await callback.message.answer(
        f"{from_meta['flag']} {from_meta['label']} ({lang_from_code}) → "
        f"{to_meta['flag']} {to_meta['label']} ({lang_to_code})\n\n"
        f"{texts['pair_configured']}",
    )
    await callback.answer()