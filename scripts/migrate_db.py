import sqlite3
import chromadb
from chromadb.config import Settings
import os
import shutil

old_db_path = "./data/turkish_recipes_db"
new_db_path = "./data/turkish_recipes_db_fixed"

print(f"Starting migration from {old_db_path} to {new_db_path}...")

# 1. Ensure new path is clean
if os.path.exists(new_db_path):
    shutil.rmtree(new_db_path)
os.makedirs(new_db_path)

try:
    # 2. Extract data from old SQLite
    print("Extracting data from old SQLite...")
    conn = sqlite3.connect(os.path.join(old_db_path, "chroma.sqlite3"))
    cursor = conn.cursor()
    
    # In Chroma 0.4+, documents are often in 'embedding_fulltext' or 'embeddings'
    # Actually, the most reliable way is to join 'embeddings' and 'embeddings_queue' or similar
    # But usually just SELECT * FROM embeddings works for basic fields
    cursor.execute("SELECT id, document, metadata FROM embeddings")
    rows = cursor.fetchall()
    print(f"Extracted {len(rows)} records.")

    # 3. Setup new Chroma with SentenceTransformer
    print("Initializing new ChromaDB...")
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    emb_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    client = chromadb.PersistentClient(path=new_db_path, settings=Settings(anonymized_telemetry=False))
    collection = client.create_collection(
        name="turkish_recipes_collection",
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # 4. Re-index in batches
    batch_size = 100
    import json
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        ids = [r[0] for r in batch]
        documents = [r[1] for r in batch]
        metadatas = [json.loads(r[2]) if r[2] else {} for r in batch]
        
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"Indexed {min(i + batch_size, len(rows))}/{len(rows)}...")

    print("\nSUCCESS: Migration complete!")
    print(f"Please update .env CHROMA_PERSIST_DIR to: {new_db_path}")

except Exception as e:
    print("\nFAILURE!")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
