from typing import Optional

from langdetect import detect, DetectorFactory, LangDetectException

DetectorFactory.seed = 0

SUPPORTED_LANGS = {"RU", "EN", "VI"}

ISO_TO_APP = {
    "ru": "RU",
    "en": "EN",
    "vi": "VI",
    "vn": "VI",
}


def detect_language(text: str) -> Optional[str]:
    """
    Detect language of text and map to RU/EN/VI if possible.
    Returns: "RU", "EN", "VI" or None if not recognized.
    """
    text = (text or "").strip()
    if not text:
        return None

    try:
        iso_code = detect(text)
    except LangDetectException:
        return None

    return ISO_TO_APP.get(iso_code)