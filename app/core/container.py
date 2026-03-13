"""
Dependency Injection Container

Bu modül, FastAPI'nin Depends mekanizmasıyla entegre çalışan
dependency factory fonksiyonlarını içerir.

Kullanım:
    from app.core.container import get_recipe_service
    
    @router.post("/")
    async def create_recipe(
        data: RecipeCreate,
        service: RecipeService = Depends(get_recipe_service)
    ):
        return await service.create(data)
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories import RecipeRepository
from app.services import RecipeService, VectorStoreService, RAGService


def get_recipe_repository(
    db: AsyncSession = Depends(get_db),
) -> RecipeRepository:
    """RecipeRepository dependency factory."""
    return RecipeRepository(db)


def get_vector_service() -> VectorStoreService:
    """VectorStoreService dependency factory (singleton-like)."""
    return VectorStoreService()


def get_recipe_service(
    repo: RecipeRepository = Depends(get_recipe_repository),
    vector_svc: VectorStoreService = Depends(get_vector_service),
) -> RecipeService:
    """RecipeService dependency factory with injected dependencies."""
    return RecipeService(repo, vector_svc)


def get_rag_service(
    vector_svc: VectorStoreService = Depends(get_vector_service),
) -> RAGService:
    """RAGService dependency factory."""
    return RAGService(vector_svc)
