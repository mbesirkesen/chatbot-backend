from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.config import get_settings
from app.core.logging import logger
from app.domain.interfaces import IVectorStore
from app.services.translation import translate_query_for_search, get_no_result_message

settings = get_settings()

RAG_SYSTEM_PROMPT = """\
Sen yardımsever bir yemek tarifi asistanısın. Veritabanındaki tarifler İngilizce.

ÖNEMLİ KURALLAR:
1. HER ZAMAN Türkçe cevap ver.
2. Bulunan tarifi mutlaka öner - pozitif ve yardımcı ol!
3. "Tarif yok" veya "eşleşmiyor" deme - bunun yerine tarifi nasıl kullanabileceklerini açıkla.
4. Tarifi öneri olarak sun: "Size şu tarifi buldum" veya "İşte beğenebileceğiniz bir tarif"

Tarifi sunarken şunları ekle:
- Tarif adı (Türkçe)
- Malzemeler - açıkça listele (Türkçe)
- Yapılışı - adım adım (Türkçe)
- Hazırlık/pişirme süresi, porsiyon, zorluk varsa

Kullanıcı önceki bağlama atıfta bulunursa ("şunu", "bunu"), sohbet geçmişini kullan.

### Bulunan tarif:
{context}
"""

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", RAG_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
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

    def _build_search_query(self, question: str, history: list[dict]) -> str:
        """
        Takip mesajları için ('şunu yapmak istiyorum' vb.) önceki bağlamı ekler.
        Vektör aramasında daha iyi eşleşme sağlar.
        """
        if not history:
            return question
        last_user = None
        for m in reversed(history):
            if m.get("role") == "user":
                last_user = m.get("content", "").strip()
                break
        if last_user and last_user != question:
            return f"{last_user} {question}"
        return question

    async def ask(
        self,
        question: str,
        history: list[dict] | None = None,
        n_results: int = 5,
    ) -> dict:
        """
        Kullanıcı sorusuna RAG ile yanıt verir. Sohbet geçmişi varsa bağlama dahil eder.
        
        Args:
            question: Kullanıcı sorusu
            history: Önceki mesajlar [{"role":"user"|"assistant","content":"..."}]
            n_results: Vektör aramasında döndürülecek sonuç sayısı
            
        Returns:
            answer: LLM yanıtı
            source_ids: Kullanılan kaynak tarif ID'leri
        """
        history = history or []
        logger.info("RAG sorgusu: '%s' (geçmiş: %d mesaj)", question, len(history))

        combined_for_search = self._build_search_query(question, history)
        search_query = await translate_query_for_search(combined_for_search)
        relevant_docs = await self._vector_store.search(search_query, n_results=n_results)

        if not relevant_docs:
            logger.warning("Vektör aramasında sonuç bulunamadı: '%s'", question)
            return {
                "answer": get_no_result_message(question),
                "source_ids": [],
                "documents": [],
            }

        best_match = relevant_docs[0]
        context = best_match["text"]

        from langchain_core.messages import HumanMessage, AIMessage
        history_msgs = []
        for m in history:
            if m.get("role") == "user":
                history_msgs.append(HumanMessage(content=m.get("content", "")))
            elif m.get("role") == "assistant":
                history_msgs.append(AIMessage(content=m.get("content", "")))

        llm = self._get_llm()
        chain = rag_prompt | llm

        response = await chain.ainvoke({
            "context": context,
            "history": history_msgs,
            "question": question,
        })

        logger.info(
            "RAG cevabı oluşturuldu: en alakalı tarif '%s'",
            best_match.get("metadata", {}).get("title", best_match["id"]),
        )

        return {
            "answer": response.content,
            "source_ids": [best_match["id"]],
            "documents": [best_match],
        }
