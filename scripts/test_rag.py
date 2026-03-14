import asyncio
import os
import sys

# Ensure app is in path
sys.path.append(os.getcwd())

from app.services.rag_service import RAGService
from app.services.vector_store import VectorStoreService
from app.core.config import get_settings

async def test_rag():
    settings = get_settings()
    print(f"Testing RAG with model: {settings.GEMINI_MODEL}")
    print(f"Embedding Provider: {settings.EMBEDDING_PROVIDER}")
    
    try:
        vector_store = VectorStoreService()
        rag_service = RAGService(vector_store)
        
        print("Testing a simple query...")
        result = await rag_service.ask("Merhaba, bana bir yemek önerir misin?")
        
        print("\nSUCCESS!")
        print(f"Answer: {result['answer'][:100]}...")
        print(f"Sources found: {len(result['source_ids'])}")
        
    except Exception as e:
        print("\nFAILURE!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag())
