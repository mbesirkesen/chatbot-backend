import chromadb
from chromadb.config import Settings
import os

db_path = "./data/turkish_recipes_db"
print(f"Opening Chroma at {db_path}...")

try:
    client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
    collections = client.list_collections()
    print("Collections:", [c.name for c in collections])
    
    if collections:
        coll = collections[0]
        print(f"Peeking into collection: {coll.name}")
        print(f"Count: {coll.count()}")
        
        #peek = coll.peek(1)
        # We use get() instead of peek() to avoid using the index if possible
        data = coll.get(limit=1, include=['documents', 'metadatas'])
        print("Data sample (ID):", data['ids'][0])
        print("Data sample (Text):", data['documents'][0][:100])
        
    print("\nSUCCESS: Data is accessible!")

except Exception as e:
    print("\nFAILURE!")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
