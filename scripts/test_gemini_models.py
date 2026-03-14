"""
Gemini API modellerini test eder.
.env'deki GEMINI_API_KEY ile hangi modellerin çalıştığını kontrol eder.
"""
import asyncio
import os
from pathlib import Path

# Proje kökünden .env yükle
root = Path(__file__).resolve().parent.parent
os.chdir(root)

from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

# Test edilecek modeller (Free tier'da genelde kullanılabilir)
MODELS_TO_TEST = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
]

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("HATA: .env'de GEMINI_API_KEY tanımlı değil")
    exit(1)


async def test_model(model_name: str) -> tuple[str, bool, str]:
    """Tek modeli test et. (model, başarılı_mı, mesaj) döner."""
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=API_KEY,
            temperature=0,
        )
        response = await llm.ainvoke("Say 'test OK' in one word.")
        return (model_name, True, str(response.content)[:50])
    except Exception as e:
        err = str(e)
        if "429" in err or "ResourceExhausted" in err or "quota" in err.lower():
            return (model_name, False, "Kota/limit aşıldı")
        if "404" in err or "not found" in err.lower():
            return (model_name, False, "Model bulunamadı")
        if "403" in err or "permission" in err.lower():
            return (model_name, False, "Yetki/erişim yok")
        return (model_name, False, err[:80])


async def main():
    print("Gemini API Model Testi")
    print("=" * 50)
    print(f"API Key (ilk 10 char): {API_KEY[:10]}...")
    print()

    results = []
    for model in MODELS_TO_TEST:
        name, ok, msg = await test_model(model)
        results.append((name, ok, msg))
        status = "[OK] CALISIYOR" if ok else f"[FAIL] {msg}"
        print(f"  {name}: {status}")

    print()
    print("=" * 50)
    working = [r[0] for r in results if r[1]]
    if working:
        print(f"Kullanılabilir modeller: {', '.join(working)}")
        print()
        print(".env dosyana ekle:")
        print(f"  GEMINI_MODEL={working[0]}")
    else:
        print("Hiçbir model çalışmadı. API key veya kota kontrol et.")
        print("https://aistudio.google.com/rate-limit adresinden limitleri kontrol et.")


if __name__ == "__main__":
    asyncio.run(main())
