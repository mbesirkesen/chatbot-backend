import asyncio
import os
import sys

# Ensure app is in path
sys.path.append(os.getcwd())

from app.services.vector_store import VectorStoreService
from app.core.config import get_settings

async def debug_chroma():
    settings = get_settings()
    print(f"Chroma Path: {settings.CHROMA_PERSIST_DIR}")
    print(f"Collection Name: {settings.CHROMA_COLLECTION_NAME}")
    
    try:
        vs = VectorStoreService()
        client = vs._get_client()
        print("Collections in DB:", client.list_collections())
        
        collection = vs._get_collection()
        print(f"Active Collection: {collection.name}")
        print(f"Document Count: {collection.count()}")
        
        if collection.count() > 0:
            peek = collection.peek(1)
            print("Peek (first document):", peek['documents'][0][:100])
            print("Peek metadatas:", peek['metadatas'][0])
            
        print("\nSUCCESS: Database loaded correctly.")
        
    except Exception as e:
        print("\nFAILURE!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_chroma())
