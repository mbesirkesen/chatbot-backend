from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import get_settings
from app.core.logging import logger
from app.domain.interfaces import IVectorStore
from app.services.translation import translate_query_for_search, get_no_result_message

settings = get_settings()

RAG_SYSTEM_PROMPT = """\
You are a helpful recipe assistant. The recipe database is in English.
Answer the user's question based ONLY on the recipes below.
If the recipes don't contain enough relevant info, say so honestly.

IMPORTANT: Respond in the SAME LANGUAGE the user wrote their question in.
(e.g. Turkish question -> Turkish answer, English question -> English answer)

### Recipes found:
{context}
"""

RAG_USER_PROMPT = "{question}"

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", RAG_SYSTEM_PROMPT),
    ("human", RAG_USER_PROMPT),
])


class RAGService:
    """
    RAG (Retrieval-Augmented Generation) servisi.
    
    Kullanıcı sorularını vektör aramasıyla zenginleştirip
    LLM'e gönderir.
    """

    def __init__(self, vector_store: IVectorStore):
        self._vector_store = vector_store

    def _get_llm(self) -> ChatGoogleGenerativeAI:
        """LLM instance döner."""
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
            max_output_tokens=2048,
        )

    async def ask(self, question: str, n_results: int = 5) -> dict:
        """
        Kullanıcı sorusuna RAG ile yanıt verir.
        
        Args:
            question: Kullanıcı sorusu
            n_results: Vektör aramasında döndürülecek sonuç sayısı
            
        Returns:
            answer: LLM yanıtı
            source_ids: Kullanılan kaynak tarif ID'leri
        """
        logger.info("RAG sorgusu başlatıldı: '%s'", question)

        search_query = await translate_query_for_search(question)
        relevant_docs = await self._vector_store.search(search_query, n_results=n_results)

        if not relevant_docs:
            logger.warning("Vektör aramasında sonuç bulunamadı: '%s'", question)
            return {
                "answer": get_no_result_message(question),
                "source_ids": [],
            }

        context = "\n\n---\n\n".join(doc["text"] for doc in relevant_docs)

        llm = self._get_llm()
        chain = rag_prompt | llm

        response = await chain.ainvoke({
            "context": context,
            "question": question,
        })

        source_ids = [doc["id"] for doc in relevant_docs]
        logger.info(
            "RAG cevabı oluşturuldu: %d kaynak kullanıldı",
            len(source_ids),
        )

        return {
            "answer": response.content,
            "source_ids": source_ids,
        }
