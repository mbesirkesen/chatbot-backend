from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_recipe_service, get_recipe_or_404
from app.models.recipe import Recipe
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipeSearchQuery,
)
from app.services import RecipeService

router = APIRouter(prefix="/recipes", tags=["Tarifler"])


@router.post("/", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    data: RecipeCreate,
    service: RecipeService = Depends(get_recipe_service),
):
    """Yeni tarif oluşturur."""
    return await service.create(data)


@router.get("/", response_model=list[RecipeResponse])
async def list_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: RecipeService = Depends(get_recipe_service),
):
    """Tüm tarifleri listeler."""
    return await service.get_all(skip=skip, limit=limit)


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe: Recipe = Depends(get_recipe_or_404),
):
    """ID ile tarif getirir."""
    return recipe


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    data: RecipeUpdate,
    recipe: Recipe = Depends(get_recipe_or_404),
    service: RecipeService = Depends(get_recipe_service),
):
    """Tarifi günceller."""
    return await service.update(recipe.id, data)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe: Recipe = Depends(get_recipe_or_404),
    service: RecipeService = Depends(get_recipe_service),
):
    """Tarifi siler."""
    await service.delete(recipe.id)


@router.post("/search", response_model=list[RecipeResponse])
async def search_recipes(
    search: RecipeSearchQuery,
    service: RecipeService = Depends(get_recipe_service),
):
    """Tariflerde arama yapar."""
    return await service.search(
        query=search.query,
        ingredients=search.ingredients,
        cuisine=search.cuisine,
        category=search.category,
        limit=search.limit,
    )
