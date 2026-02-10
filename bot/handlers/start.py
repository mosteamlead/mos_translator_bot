from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db.storage import set_lang_from, set_lang_to, get_user_languages

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


@router.message(CommandStart())
async def cmd_start(message: Message):
    await set_lang_from(message.from_user.id, lang_from="")
    await message.answer(
        "Hi! I am a bilingual translator bot.\n\n"
        "First, choose your **first language**:",
        reply_markup=build_first_lang_keyboard(),
    )


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
        "- Other languages → I translate to the first language.",
    )
    await callback.answer()