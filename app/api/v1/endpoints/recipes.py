import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import logger
from app.models.recipe import Recipe
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipeSearchQuery,
)
from app.services.recipe_service import RecipeService
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/recipes", tags=["Tarifler"])


@router.post("/", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    data: RecipeCreate,
    db: AsyncSession = Depends(get_db),
):
    recipe = await RecipeService.create(db, data)

    try:
        await VectorStoreService.add_recipe(
            recipe_id=str(recipe.id),
            text=recipe.to_document_text(),
            metadata={"title": recipe.title, "cuisine": recipe.cuisine or ""},
        )
    except Exception as e:
        logger.error("Vektör veritabanına ekleme başarısız: %s", e)

    return recipe


@router.get("/", response_model=list[RecipeResponse])
async def list_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await RecipeService.get_all(db, skip=skip, limit=limit)


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    recipe = await RecipeService.get_by_id(db, recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarif bulunamadı",
        )
    return recipe


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: uuid.UUID,
    data: RecipeUpdate,
    db: AsyncSession = Depends(get_db),
):
    recipe = await RecipeService.update(db, recipe_id, data)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarif bulunamadı",
        )

    try:
        await VectorStoreService.add_recipe(
            recipe_id=str(recipe.id),
            text=recipe.to_document_text(),
            metadata={"title": recipe.title, "cuisine": recipe.cuisine or ""},
        )
    except Exception as e:
        logger.error("Vektör veritabanı güncelleme başarısız: %s", e)

    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    deleted = await RecipeService.delete(db, recipe_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarif bulunamadı",
        )

    try:
        await VectorStoreService.delete_recipe(str(recipe_id))
    except Exception as e:
        logger.error("Vektör veritabanından silme başarısız: %s", e)


@router.post("/search", response_model=list[RecipeResponse])
async def search_recipes(
    search: RecipeSearchQuery,
    db: AsyncSession = Depends(get_db),
):
    results = await RecipeService.search(
        db,
        query=search.query,
        ingredients=search.ingredients,
        cuisine=search.cuisine,
        category=search.category,
        limit=search.limit,
    )
    return results
