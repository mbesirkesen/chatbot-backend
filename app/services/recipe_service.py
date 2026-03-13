import uuid

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.recipe import Recipe
from app.schemas.recipe import RecipeCreate, RecipeUpdate


class RecipeService:

    @staticmethod
    async def create(db: AsyncSession, data: RecipeCreate) -> Recipe:
        recipe = Recipe(**data.model_dump())
        db.add(recipe)
        await db.flush()
        await db.refresh(recipe)
        logger.info("Yeni tarif oluşturuldu: %s (id=%s)", recipe.title, recipe.id)
        return recipe

    @staticmethod
    async def get_by_id(db: AsyncSession, recipe_id: uuid.UUID) -> Recipe | None:
        result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession, skip: int = 0, limit: int = 20
    ) -> list[Recipe]:
        result = await db.execute(
            select(Recipe).order_by(Recipe.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession, recipe_id: uuid.UUID, data: RecipeUpdate
    ) -> Recipe | None:
        recipe = await RecipeService.get_by_id(db, recipe_id)
        if not recipe:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(recipe, field, value)

        await db.flush()
        await db.refresh(recipe)
        logger.info("Tarif güncellendi: %s (id=%s)", recipe.title, recipe.id)
        return recipe

    @staticmethod
    async def delete(db: AsyncSession, recipe_id: uuid.UUID) -> bool:
        recipe = await RecipeService.get_by_id(db, recipe_id)
        if not recipe:
            return False
        await db.delete(recipe)
        await db.flush()
        logger.info("Tarif silindi: id=%s", recipe_id)
        return True

    @staticmethod
    async def search_by_title(
        db: AsyncSession, query: str, limit: int = 10
    ) -> list[Recipe]:
        result = await db.execute(
            select(Recipe)
            .where(func.lower(Recipe.title).contains(query.lower()))
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def search_by_ingredients(
        db: AsyncSession, ingredients: list[str], limit: int = 10
    ) -> list[Recipe]:
        """Verilen malzemelerden herhangi birini içeren tarifleri bulur."""
        conditions = [
            Recipe.ingredients.any(func.lower(ing.lower()))
            for ing in ingredients
        ]
        result = await db.execute(
            select(Recipe).where(or_(*conditions)).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def search(
        db: AsyncSession,
        query: str | None = None,
        ingredients: list[str] | None = None,
        cuisine: str | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> list[Recipe]:
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
            ingredient_conditions = [
                Recipe.ingredients.any(func.lower(ing.lower()))
                for ing in ingredients
            ]
            filters.append(or_(*ingredient_conditions))
        if cuisine:
            filters.append(func.lower(Recipe.cuisine) == cuisine.lower())
        if category:
            filters.append(func.lower(Recipe.category) == category.lower())

        if filters:
            stmt = stmt.where(*filters)

        result = await db.execute(stmt.limit(limit))
        return list(result.scalars().all())
