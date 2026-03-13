from fastapi import APIRouter

from app.api.v1.endpoints import recipes, chat

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(recipes.router)
api_router.include_router(chat.router)
