import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import logger
from app.schemas.recipe import ChatRequest, ChatResponse, RecipeResponse
from app.api.dependencies import get_rag_service, get_recipe_service
from app.services import RAGService, RecipeService

router = APIRouter(prefix="/chat", tags=["Sohbet"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
    recipe_service: RecipeService = Depends(get_recipe_service),
):
    """Kullanıcı mesajına RAG ile yanıt verir."""
    logger.info("Yeni sohbet mesajı: '%s'", request.message)

    history = [{"role": m.role, "content": m.content} for m in request.history]
    try:
        rag_result = await rag_service.ask(request.message, history=history)
    except Exception as e:
        logger.error("RAG servisi hatası: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Yapay zeka servisi şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin.",
        )

    sources: list[RecipeResponse] = []
    for source_id in rag_result.get("source_ids", []):
        try:
            recipe = await recipe_service.get_by_id(uuid.UUID(source_id))
            if recipe:
                sources.append(RecipeResponse.model_validate(recipe))
        except (ValueError, Exception) as e:
            logger.warning("Kaynak tarif yüklenemedi (id=%s): %s", source_id, e)

    return ChatResponse(
        answer=rag_result["answer"],
        sources=sources,
    )
