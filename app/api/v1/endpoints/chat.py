from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import logger
from app.schemas.recipe import ChatRequest, ChatResponse, SimpleRecipeResponse
from app.api.dependencies import get_rag_service
from app.services import RAGService

router = APIRouter(prefix="/chat", tags=["Sohbet"])


def parse_recipe_from_document(doc: dict) -> SimpleRecipeResponse:
    """ChromaDB dökümanından tarif bilgilerini parse eder."""
    text = doc.get("text", "")
    metadata = doc.get("metadata", {})
    
    ingredients: list[str] = []
    instructions = ""
    
    ing_start = -1
    for marker in ["Malzemeler / Ingredients:", "Ingredients:", "Malzemeler:"]:
        if marker in text:
            ing_start = text.find(marker) + len(marker)
            break
    
    dir_start = -1
    for marker in ["Yapılışı / Directions:", "Directions:", "Instructions:", "Yapılışı:"]:
        if marker in text:
            dir_start = text.find(marker) + len(marker)
            break
    
    if ing_start > 0:
        if dir_start > ing_start:
            ing_section = text[ing_start:text.find("Yapılışı") if "Yapılışı" in text else text.find("Directions")]
        else:
            ing_section = text[ing_start:]
        
        ing_text = ing_section.strip()
        if "," in ing_text and "\n" not in ing_text:
            ingredients = [i.strip() for i in ing_text.split(",") if i.strip()]
        else:
            ingredients = [line.strip().lstrip("- ").lstrip("* ").lstrip("0123456789.") 
                          for line in ing_text.split("\n") if line.strip()]
    
    if dir_start > 0:
        instructions = text[dir_start:].strip()
        for sep in [", ", ". "]:
            if sep in instructions and instructions.count(sep) >= 2:
                steps = [s.strip() for s in instructions.replace(sep, ".\n").split("\n") if s.strip()]
                instructions = "\n".join(steps)
                break
    
    return SimpleRecipeResponse(
        id=doc.get("id", ""),
        title=metadata.get("title", "Tarif"),
        description=metadata.get("description"),
        ingredients=ingredients[:20] if ingredients else ["Malzeme bilgisi mevcut değil"],
        instructions=instructions[:1500] if instructions else text[:1500],
        cuisine=metadata.get("cuisine"),
        category=metadata.get("category") or "Genel",
        prep_time_minutes=metadata.get("prep_time_minutes"),
        cook_time_minutes=metadata.get("cook_time_minutes"),
        servings=metadata.get("servings"),
        difficulty=metadata.get("difficulty"),
        rating=metadata.get("rating"),
    )


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
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

    sources: list[SimpleRecipeResponse] = []
    for doc in rag_result.get("documents", []):
        try:
            recipe = parse_recipe_from_document(doc)
            sources.append(recipe)
        except Exception as e:
            logger.warning("Tarif parse edilemedi: %s", e)

    logger.info("Chat yanıtı hazır: %d kaynak tarif", len(sources))

    return ChatResponse(
        answer=rag_result["answer"],
        sources=sources,
    )
