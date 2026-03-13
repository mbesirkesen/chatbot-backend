import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import logger
from app.schemas.recipe import ChatRequest, ChatResponse, RecipeResponse
from app.services.rag_service import RAGService
from app.services.recipe_service import RecipeService

router = APIRouter(prefix="/chat", tags=["Sohbet"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    logger.info("Yeni sohbet mesajı: '%s'", request.message)

    try:
        rag_result = await RAGService.ask(request.message)
    except Exception as e:
        logger.error("RAG servisi hatası: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Yapay zeka servisi şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin.",
        )

    sources: list[RecipeResponse] = []
    for source_id in rag_result.get("source_ids", []):
        try:
            recipe = await RecipeService.get_by_id(db, uuid.UUID(source_id))
            if recipe:
                sources.append(RecipeResponse.model_validate(recipe))
        except (ValueError, Exception) as e:
            logger.warning("Kaynak tarif yüklenemedi (id=%s): %s", source_id, e)

    return ChatResponse(
        answer=rag_result["answer"],
        sources=sources,
    )
