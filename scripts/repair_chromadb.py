"""
ChromaDB Repair Script

Bozuk ChromaDB veritabanını SQLite'tan okuyup yeniden oluşturur.
"""

import sys
import sqlite3
import os
import shutil

def log(msg):
    print(msg, flush=True)

log("Script baslatiliyor...")
log("ChromaDB import ediliyor...")

import chromadb
from chromadb.config import Settings as ChromaSettings

log("ChromaDB import edildi.")


DB_PATH = "./data/turkish_recipes_db_backup/chroma.sqlite3"
NEW_DB_PATH = "./data/turkish_recipes_db"
COLLECTION_NAME = "turkish_recipes_collection"


def inspect_and_extract():
    """SQLite veritabanından dokümanları ve metadata'yı çıkar"""
    log("=" * 60)
    log("Veriler Cikariliyor...")
    log("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # embedding_id'leri al
    cursor.execute("SELECT DISTINCT embedding_id FROM embeddings")
    embedding_ids = [row[0] for row in cursor.fetchall()]
    log(f"Toplam {len(embedding_ids)} embedding ID bulundu")
    
    # Dokümanları al (embedding_fulltext_search_content tablosundan)
    cursor.execute("""
        SELECT e.embedding_id, efs.c0 
        FROM embeddings e
        JOIN embedding_fulltext_search_content efs ON e.id = efs.id
    """)
    documents = {row[0]: row[1] for row in cursor.fetchall()}
    log(f"Toplam {len(documents)} dokuman bulundu")
    
    # Metadata'yı al
    cursor.execute("""
        SELECT e.embedding_id, em.key, em.string_value, em.int_value, em.float_value
        FROM embeddings e
        JOIN embedding_metadata em ON e.id = em.id
    """)
    
    metadata = {}
    for row in cursor.fetchall():
        emb_id = row[0]
        key = row[1]
        value = row[2] or row[3] or row[4]
        if emb_id not in metadata:
            metadata[emb_id] = {}
        metadata[emb_id][key] = value
    
    log(f"Toplam {len(metadata)} metadata kaydi bulundu")
    
    # İlk birkaç dokümanı göster
    log("\nOrnek dokumanlar:")
    for i, (emb_id, doc) in enumerate(list(documents.items())[:2]):
        log(f"\n  [{i+1}] ID: {emb_id}")
        log(f"      Dokuman: {doc[:150]}...")
    
    conn.close()
    
    # Kayıtları hazırla
    records = []
    for emb_id in embedding_ids:
        doc = documents.get(emb_id, "")
        if doc:  # Sadece dokümanı olanları al
            # Reserved key'leri filtrele
            meta = metadata.get(emb_id, {})
            clean_meta = {k: v for k, v in meta.items() if not k.startswith("chroma:")}
            records.append({
                "id": emb_id,
                "document": doc,
                "metadata": clean_meta
            })
    
    return records


def rebuild_with_new_embeddings(records):
    """Yeni ChromaDB oluştur ve verileri Google Embeddings ile yeniden indexle"""
    log("Langchain import ediliyor...")
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from dotenv import load_dotenv
    import time
    
    load_dotenv()
    
    log("\n" + "=" * 60)
    log("Yeni ChromaDB Olusturuluyor...")
    log("=" * 60)
    
    # Yeni DB dizinini temizle
    if os.path.exists(NEW_DB_PATH):
        shutil.rmtree(NEW_DB_PATH)
        log(f"Eski veritabani silindi: {NEW_DB_PATH}")
    
    # Yeni client oluştur
    client = chromadb.PersistentClient(
        path=NEW_DB_PATH,
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    
    # Koleksiyon oluştur
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    log(f"Koleksiyon olusturuldu: {COLLECTION_NAME}")
    
    # Google Embeddings
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log("HATA: GEMINI_API_KEY bulunamadi!")
        return
    
    log("Google Embeddings modeli yukleniyor...")
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )
    log("Model hazir!")
    
    log(f"\nToplam {len(records)} kayit islenecek...")
    log("Rate limit korumasi aktif - gerektiginde bekleyecek\n")
    
    # Batch halinde işle
    batch_size = 20  # Daha küçük batch
    total = len(records)
    failed_batches = []
    
    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        
        ids = [r["id"] for r in batch]
        documents = [r["document"] for r in batch]
        metadatas = [r["metadata"] for r in batch]
        
        # Embedding oluştur - retry logic ile
        max_retries = 5
        for attempt in range(max_retries):
            try:
                vectors = embeddings_model.embed_documents(documents)
                
                # ChromaDB'ye ekle
                collection.add(
                    ids=ids,
                    embeddings=vectors,
                    documents=documents,
                    metadatas=metadatas
                )
                break  # Başarılı, döngüden çık
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    # Rate limit - bekle ve tekrar dene
                    wait_time = 60 * (attempt + 1)  # 60, 120, 180, 240, 300 saniye
                    log(f"  Rate limit! {wait_time}s bekleniyor... (deneme {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    log(f"  Hata (batch {i//batch_size + 1}): {e}")
                    failed_batches.append(i)
                    break
        
        progress = min(i + batch_size, total)
        log(f"Ilerleme: {progress}/{total} ({100*progress//total}%) - DB'de: {collection.count()}")
        
        # Her batch sonrası kısa bekleme
        time.sleep(1)
    
    log(f"\n{'='*60}")
    log(f"TAMAMLANDI!")
    log(f"{'='*60}")
    log(f"Yeni veritabani: {NEW_DB_PATH}")
    log(f"Koleksiyondaki kayit sayisi: {collection.count()}")
    
    if failed_batches:
        log(f"\nBasarisiz batch'ler: {len(failed_batches)}")


if __name__ == "__main__":
    # 1. Verileri çıkar
    records = inspect_and_extract()
    
    if not records:
        log("Kayit bulunamadi!")
        exit(1)
    
    # Sadece ilk 1000 kayıt
    MAX_RECORDS = 1000
    records = records[:MAX_RECORDS]
    
    log(f"\n{len(records)} kayit bulundu. Yeniden indexleme basliyor...")
    
    # 2. Yeniden indexle
    rebuild_with_new_embeddings(records)
