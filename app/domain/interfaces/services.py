from typing import Protocol, runtime_checkable


@runtime_checkable
class IVectorStore(Protocol):
    """Vektör veritabanı servisi interface."""

    async def add_recipe(self, recipe_id: str, text: str, metadata: dict | None = None) -> None:
        """Tarifi vektör veritabanına ekler/günceller."""
        ...

    async def search(self, query: str, n_results: int = 5) -> list[dict]:
        """Sorguya benzer dokümanları arar."""
        ...

    async def delete_recipe(self, recipe_id: str) -> None:
        """Tarifi vektör veritabanından siler."""
        ...

    async def sync_recipe(self, recipe) -> None:
        """Tarifi vektör veritabanıyla senkronize eder."""
        ...


@runtime_checkable
class IRAGService(Protocol):
    """RAG (Retrieval-Augmented Generation) servisi interface."""

    async def ask(self, question: str, n_results: int = 5) -> dict:
        """Kullanıcı sorusuna RAG ile yanıt verir."""
        ...
