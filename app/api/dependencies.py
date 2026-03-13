from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.recipe import Recipe
from app.repositories import RecipeRepository
from app.services.recipe_service import RecipeService
from app.services.vector_store import VectorStoreService
from app.services.rag_service import RAGService


def get_recipe_repository(
    db: AsyncSession = Depends(get_db),
) -> RecipeRepository:
    """RecipeRepository dependency."""
    return RecipeRepository(db)


def get_vector_service() -> VectorStoreService:
    """VectorStoreService dependency (singleton-like)."""
    return VectorStoreService()


def get_recipe_service(
    repo: RecipeRepository = Depends(get_recipe_repository),
    vector_svc: VectorStoreService = Depends(get_vector_service),
) -> RecipeService:
    """RecipeService dependency with injected dependencies."""
    return RecipeService(repo, vector_svc)


def get_rag_service(
    vector_svc: VectorStoreService = Depends(get_vector_service),
) -> RAGService:
    """RAGService dependency."""
    return RAGService(vector_svc)


async def get_recipe_or_404(
    recipe_id: UUID,
    service: RecipeService = Depends(get_recipe_service),
) -> Recipe:
    """
    Tarifi getirir, bulunamazsa 404 hatası fırlatır.
    
    Bu dependency, tekrarlayan 404 kontrollerini ortadan kaldırır.
    
    Kullanım:
        @router.get("/{recipe_id}")
        async def get_recipe(recipe: Recipe = Depends(get_recipe_or_404)):
            return recipe
    """
    recipe = await service.get_by_id(recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarif bulunamadı",
        )
    return recipe
