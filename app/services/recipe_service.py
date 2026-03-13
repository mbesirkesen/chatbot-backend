from uuid import UUID

from app.core.logging import logger
from app.models.recipe import Recipe
from app.schemas.recipe import RecipeCreate, RecipeUpdate
from app.repositories import RecipeRepository
from app.services.decorators import sync_to_vector_store
from app.domain.interfaces import IVectorStore


class RecipeService:
    """
    Tarif iş mantığı servisi.
    
    Repository pattern ve Dependency Injection kullanarak
    SOLID prensiplerine uygun tasarlanmıştır.
    """

    def __init__(
        self,
        repo: RecipeRepository,
        vector_svc: IVectorStore | None = None,
    ):
        self._repo = repo
        self._vector_svc = vector_svc

    async def get_by_id(self, recipe_id: UUID) -> Recipe | None:
        """ID ile tarif getirir."""
        return await self._repo.get_by_id(recipe_id)

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Recipe]:
        """Tüm tarifleri sayfalı olarak getirir."""
        return await self._repo.get_all(skip=skip, limit=limit)

    @sync_to_vector_store
    async def create(self, data: RecipeCreate) -> Recipe:
        """
        Yeni tarif oluşturur.
        
        @sync_to_vector_store decorator'ı sayesinde otomatik olarak
        vektör veritabanıyla senkronize edilir.
        """
        recipe = await self._repo.create(data)
        logger.info("Yeni tarif oluşturuldu: %s (id=%s)", recipe.title, recipe.id)
        return recipe

    @sync_to_vector_store
    async def update(self, recipe_id: UUID, data: RecipeUpdate) -> Recipe | None:
        """
        Tarifi günceller.
        
        @sync_to_vector_store decorator'ı sayesinde otomatik olarak
        vektör veritabanıyla senkronize edilir.
        """
        recipe = await self._repo.update(recipe_id, data)
        if recipe:
            logger.info("Tarif güncellendi: %s (id=%s)", recipe.title, recipe.id)
        return recipe

    async def delete(self, recipe_id: UUID) -> bool:
        """Tarifi siler ve vektör veritabanından kaldırır."""
        deleted = await self._repo.delete(recipe_id)
        if deleted and self._vector_svc:
            try:
                await self._vector_svc.delete_recipe(str(recipe_id))
            except Exception as e:
                logger.error("Vektör veritabanından silme başarısız: %s", e)
        return deleted

    async def search(
        self,
        query: str | None = None,
        ingredients: list[str] | None = None,
        cuisine: str | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> list[Recipe]:
        """Çoklu kriterlere göre tarif arar."""
        return await self._repo.search(
            query=query,
            ingredients=ingredients,
            cuisine=cuisine,
            category=category,
            limit=limit,
        )

    async def search_by_title(self, query: str, limit: int = 10) -> list[Recipe]:
        """Başlığa göre tarif arar."""
        return await self._repo.search_by_title(query, limit)

    async def search_by_ingredients(
        self, ingredients: list[str], limit: int = 10
    ) -> list[Recipe]:
        """Malzemelere göre tarif arar."""
        return await self._repo.search_by_ingredients(ingredients, limit)
