from uuid import UUID

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe
from app.repositories.base import BaseRepository
from app.repositories.helpers import build_ingredient_conditions


class RecipeRepository(BaseRepository[Recipe]):
    """
    Recipe entity için repository.
    
    BaseRepository'den miras alır ve Recipe'e özel
    arama metodları ekler.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(db, Recipe)

    async def search_by_title(self, query: str, limit: int = 10) -> list[Recipe]:
        """Başlığa göre tarif arar."""
        result = await self._db.execute(
            select(Recipe)
            .where(func.lower(Recipe.title).contains(query.lower()))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_by_ingredients(
        self, ingredients: list[str], limit: int = 10
    ) -> list[Recipe]:
        """Verilen malzemelerden herhangi birini içeren tarifleri bulur."""
        conditions = build_ingredient_conditions(ingredients)
        result = await self._db.execute(
            select(Recipe).where(or_(*conditions)).limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self,
        query: str | None = None,
        ingredients: list[str] | None = None,
        cuisine: str | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> list[Recipe]:
        """Çoklu kriterlere göre tarif arar."""
        stmt = select(Recipe)
        filters = []

        if query:
            filters.append(
                or_(
                    func.lower(Recipe.title).contains(query.lower()),
                    func.lower(Recipe.description).contains(query.lower()),
                )
            )

        if ingredients:
            ingredient_conditions = build_ingredient_conditions(ingredients)
            filters.append(or_(*ingredient_conditions))

        if cuisine:
            filters.append(func.lower(Recipe.cuisine) == cuisine.lower())

        if category:
            filters.append(func.lower(Recipe.category) == category.lower())

        if filters:
            stmt = stmt.where(*filters)

        result = await self._db.execute(stmt.limit(limit))
        return list(result.scalars().all())

    async def get_by_ids(self, ids: list[UUID]) -> list[Recipe]:
        """Birden fazla ID ile tarifleri getirir."""
        if not ids:
            return []
        result = await self._db.execute(
            select(Recipe).where(Recipe.id.in_(ids))
        )
        return list(result.scalars().all())
