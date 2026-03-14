import asyncio

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


class _SentenceTransformerEmbeddingAdapter:
    """all-MiniLM-L6-v2 ile uyumlu önceden oluşturulmuş ChromaDB koleksiyonları için."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)

    async def aembed_query(self, text: str) -> list[float]:
        loop = asyncio.get_event_loop()
        vector = await loop.run_in_executor(None, lambda: self._model.encode(text).tolist())
        return vector


class VectorStoreService:
    """
    ChromaDB vektör veritabanı servisi.
    
    Tarifleri embedding'lere dönüştürüp vektör veritabanında saklar
    ve benzerlik araması yapar.
    
    EMBEDDING_PROVIDER:
    - sentence_transformer: Önceden oluşturulmuş turkish_recipes vb. için (all-MiniLM-L6-v2)
    - google: Yeni koleksiyonlar veya Google embeddings ile indexlenmiş DB için
    """

    _client: chromadb.ClientAPI | None = None
    _collection: chromadb.Collection | None = None
    _embeddings: GoogleGenerativeAIEmbeddings | _SentenceTransformerEmbeddingAdapter | None = None

    def __init__(self):
        pass

    @classmethod
    def _get_embeddings(cls):
        """Embedding modeli singleton olarak döner."""
        if cls._embeddings is None:
            if settings.EMBEDDING_PROVIDER == "sentence_transformer":
                cls._embeddings = _SentenceTransformerEmbeddingAdapter(
                    settings.EMBEDDING_MODEL_SENTENCE_TRANSFORMER
                )
                logger.info("Embedding: sentence_transformer (%s)", settings.EMBEDDING_MODEL_SENTENCE_TRANSFORMER)
            elif settings.EMBEDDING_PROVIDER == "default":
                # ChromaDB uses its own default embedding function if None is passed to Collection.add
                cls._embeddings = None
                logger.info("Embedding: ChromaDB Default (all-MiniLM-L6-v2 ONNX)")
            else:
                cls._embeddings = GoogleGenerativeAIEmbeddings(
                    model=settings.EMBEDDING_MODEL,
                    google_api_key=settings.GEMINI_API_KEY,
                )
                logger.info("Embedding: Google (%s)", settings.EMBEDDING_MODEL)
        return cls._embeddings

    @classmethod
    def _get_client(cls) -> chromadb.ClientAPI:
        """ChromaDB client singleton olarak döner."""
        if cls._client is None:
            cls._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info("ChromaDB istemcisi başlatıldı: %s", settings.CHROMA_PERSIST_DIR)
        return cls._client

    @classmethod
    def _get_collection(cls) -> chromadb.Collection:
        """ChromaDB collection singleton olarak döner. Önceden oluşturulmuş DB'deki ilk koleksiyonu kullanır."""
        if cls._collection is None:
            client = cls._get_client()
            try:
                cls._collection = client.get_collection(name=settings.CHROMA_COLLECTION_NAME)
                logger.info("ChromaDB koleksiyonu hazır: '%s' (%d döküman)", settings.CHROMA_COLLECTION_NAME, cls._collection.count())
            except Exception:
                collections = client.list_collections()
                if collections:
                    cls._collection = collections[0]
                    logger.info("Mevcut koleksiyon kullanılıyor: '%s' (%d döküman)", cls._collection.name, cls._collection.count())
                else:
                    cls._collection = client.create_collection(
                        name=settings.CHROMA_COLLECTION_NAME,
                        metadata={"hnsw:space": "cosine"},
                    )
                    logger.info("Yeni koleksiyon oluşturuldu: '%s'", settings.CHROMA_COLLECTION_NAME)
        return cls._collection

    async def add_recipe(
        self, recipe_id: str, text: str, metadata: dict | None = None
    ) -> None:
        """Tarifi vektör veritabanına ekler/günceller."""
        embeddings = self._get_embeddings()
        
        vector = None
        if embeddings is not None:
             vector = await embeddings.aembed_query(text)

        collection = self._get_collection()
        collection.upsert(
            ids=[recipe_id],
            embeddings=[vector] if vector else None,
            documents=[text],
            metadatas=[metadata or {}],
        )
        logger.info("Tarif vektör veritabanına eklendi: %s", recipe_id)

    async def search(self, query: str, n_results: int = 5) -> list[dict]:
        """Sorguya benzer dokümanları arar."""
        embeddings = self._get_embeddings()
        
        collection = self._get_collection()
        
        if embeddings is not None:
            query_vector = await embeddings.aembed_query(query)
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
        else:
            # ChromaDB uses its own default embedding function
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

        documents = []
        ids = results.get("ids", [[]])
        ids_list = ids[0] if ids else []
        for i in range(len(ids_list)):
            documents.append({
                "id": ids_list[i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })

        logger.info("Vektör araması tamamlandı: '%s' -> %d sonuç", query, len(documents))
        return documents

    async def delete_recipe(self, recipe_id: str) -> None:
        """Tarifi vektör veritabanından siler."""
        collection = self._get_collection()
        collection.delete(ids=[recipe_id])
        logger.info("Tarif vektör veritabanından silindi: %s", recipe_id)

    async def sync_recipe(self, recipe) -> None:
        """
        Tarifi vektör veritabanıyla senkronize eder.
        
        Bu metod decorator tarafından otomatik çağrılır.
        """
        await self.add_recipe(
            recipe_id=str(recipe.id),
            text=recipe.to_document_text(),
            metadata={"title": recipe.title, "cuisine": recipe.cuisine or ""},
        )

    def get_collection_count(self) -> int:
        """Koleksiyondaki döküman sayısını döner."""
        return self._get_collection().count()
