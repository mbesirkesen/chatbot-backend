"""
Çok dilli destek: Veritabanı İngilizce olduğu için
kullanıcı sorusunu İngilizceye çevirip vektör aramasında kullanır.
Türkçe karakter normalizasyonu: ç/ğ/ı/ö/ş/ü hem ASCII hem de Türkçe yazımla uyumlu.
"""
import asyncio
import re
import unicodedata

from app.core.logging import logger

_NO_RESULT_MESSAGES = {
    "tr": "Bu konuda veritabanında yeterli tarif bulamadım. Lütfen farklı bir soru deneyin.",
    "en": "I couldn't find enough relevant recipes. Please try a different question.",
}

_TR_CHARS = re.compile(r"[çğıöşüÇĞİÖŞÜ]")

# Türkçe karakter → ASCII (çeviri ve arama tutarlılığı için)
_TURKISH_TO_ASCII = str.maketrans(
    "çğıöşüÇĞİÖŞÜ",
    "cgiosuCGIOSU",
)


def normalize_query(text: str) -> str:
    """
    Sorguyu normalleştirir: Unicode NFC + Türkçe karakterleri ASCII'ye çevirir.
    "çorbası" ve "corbasi" aynı forma gelir, çeviri tutarlı çalışır.
    """
    if not text or not text.strip():
        return text
    s = unicodedata.normalize("NFC", text.strip())
    return s.translate(_TURKISH_TO_ASCII)


def _translate_to_english_sync(text: str) -> str:
    """Metni İngilizceye çevirir. Önce normalize eder (TR karakter uyumu)."""
    normalized = normalize_query(text)
    if not normalized:
        return text
    try:
        from deep_translator import GoogleTranslator
        result = GoogleTranslator(source="auto", target="en").translate(text=normalized)
        if result:
            logger.debug("Sorgu çevirisi: '%s' -> '%s'", normalized[:50], result[:50])
            return result
    except Exception as e:
        logger.warning("Çeviri başarısız, orijinal kullanılıyor: %s", e)
    return normalized


def _detect_likely_lang(text: str) -> str:
    """Türkçe karakterlere göre basit dil tahmini. Varsayılan: en."""
    if not text:
        return "en"
    if _TR_CHARS.search(text):
        return "tr"
    return "en"


async def translate_query_for_search(query: str) -> str:
    """
    Vektör araması için sorguyu İngilizceye çevirir.
    Veritabanı İngilizce olduğundan eşleşme oranını artırır.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _translate_to_english_sync, query)


def get_no_result_message(user_query: str) -> str:
    """Sonuç bulunamadığında kullanıcı diline uygun mesaj döner."""
    lang = _detect_likely_lang(user_query)
    return _NO_RESULT_MESSAGES.get(lang, _NO_RESULT_MESSAGES["en"])
