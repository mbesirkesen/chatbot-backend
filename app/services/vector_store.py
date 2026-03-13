import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


class VectorStoreService:
    _client: chromadb.ClientAPI | None = None
    _collection: chromadb.Collection | None = None
    _embeddings: GoogleGenerativeAIEmbeddings | None = None

    @classmethod
    def _get_embeddings(cls) -> GoogleGenerativeAIEmbeddings:
        if cls._embeddings is None:
            cls._embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
            )
        return cls._embeddings

    @classmethod
    def _get_client(cls) -> chromadb.ClientAPI:
        if cls._client is None:
            cls._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info("ChromaDB istemcisi başlatıldı: %s", settings.CHROMA_PERSIST_DIR)
        return cls._client

    @classmethod
    def _get_collection(cls) -> chromadb.Collection:
        if cls._collection is None:
            client = cls._get_client()
            cls._collection = client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "ChromaDB koleksiyonu hazır: '%s' (%d döküman)",
                settings.CHROMA_COLLECTION_NAME,
                cls._collection.count(),
            )
        return cls._collection

    @classmethod
    async def add_recipe(cls, recipe_id: str, text: str, metadata: dict | None = None) -> None:
        embeddings = cls._get_embeddings()
        vector = await embeddings.aembed_query(text)

        collection = cls._get_collection()
        collection.upsert(
            ids=[recipe_id],
            embeddings=[vector],
            documents=[text],
            metadatas=[metadata or {}],
        )
        logger.info("Tarif vektör veritabanına eklendi: %s", recipe_id)

    @classmethod
    async def search(cls, query: str, n_results: int = 5) -> list[dict]:
        embeddings = cls._get_embeddings()
        query_vector = await embeddings.aembed_query(query)

        collection = cls._get_collection()
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        documents = []
        for i in range(len(results["ids"][0])):
            documents.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })

        logger.info("Vektör araması tamamlandı: '%s' -> %d sonuç", query, len(documents))
        return documents

    @classmethod
    async def delete_recipe(cls, recipe_id: str) -> None:
        collection = cls._get_collection()
        collection.delete(ids=[recipe_id])
        logger.info("Tarif vektör veritabanından silindi: %s", recipe_id)

    @classmethod
    def get_collection_count(cls) -> int:
        return cls._get_collection().count()
