from typing import Protocol, TypeVar, Generic, runtime_checkable
from uuid import UUID

T = TypeVar("T")


@runtime_checkable
class IRepository(Protocol[T]):
    """Generic repository interface for CRUD operations."""

    async def get_by_id(self, id: UUID) -> T | None:
        """ID ile entity getirir."""
        ...

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[T]:
        """Tüm entity'leri sayfalı olarak getirir."""
        ...

    async def create(self, data) -> T:
        """Yeni entity oluşturur."""
        ...

    async def update(self, id: UUID, data) -> T | None:
        """Entity günceller."""
        ...

    async def delete(self, id: UUID) -> bool:
        """Entity siler."""
        ...


@runtime_checkable
class IRecipeRepository(IRepository[T], Protocol[T]):
    """Recipe'e özel repository interface."""

    async def search_by_title(self, query: str, limit: int = 10) -> list[T]:
        """Başlığa göre tarif arar."""
        ...

    async def search_by_ingredients(self, ingredients: list[str], limit: int = 10) -> list[T]:
        """Malzemelere göre tarif arar."""
        ...

    async def search(
        self,
        query: str | None = None,
        ingredients: list[str] | None = None,
        cuisine: str | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> list[T]:
        """Çoklu kriterlere göre tarif arar."""
        ...
