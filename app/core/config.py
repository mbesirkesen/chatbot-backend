from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """
    Uygulama konfigürasyonu.
    
    Değerler şu öncelik sırasıyla yüklenir:
    1. Ortam değişkenleri (en yüksek öncelik)
    2. .env dosyası
    3. Varsayılan değerler (en düşük öncelik)
    
    Zorunlu alanlar (DATABASE_URL, GEMINI_API_KEY) .env'de tanımlanmalıdır.
    """

    # Sabit değerler - ortama göre değişmez
    APP_NAME: str = "Yemek Tarifi Chatbot API"
    APP_VERSION: str = "1.0.0"

    # Zorunlu - .env'den okunmalı, default yok
    DATABASE_URL: str = Field(..., description="PostgreSQL bağlantı URL'i")
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API anahtarı")

    # Opsiyonel - makul default değerler
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_COLLECTION_NAME: str = "recipes"
    EMBEDDING_MODEL: str = "models/embedding-001"
    # sentence_transformer: Önceden oluşturulmuş DB (örn. turkish_recipes) için
    # google: Yeni oluşturacağın veya Google ile indexlenmiş DB için
    EMBEDDING_PROVIDER: str = "google"
    EMBEDDING_MODEL_SENTENCE_TRANSFORMER: str = "all-MiniLM-L6-v2"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
