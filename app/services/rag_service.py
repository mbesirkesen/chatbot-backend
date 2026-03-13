from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import get_settings
from app.core.logging import logger
from app.services.vector_store import VectorStoreService

settings = get_settings()

RAG_SYSTEM_PROMPT = """\
Sen bir Türk mutfağı uzmanı yemek tarifi asistanısın. \
Kullanıcının sorularına aşağıdaki tarif bilgilerine dayanarak cevap ver. \
Eğer verilen tariflerde soruyla ilgili yeterli bilgi yoksa, bunu dürüstçe belirt. \
Cevaplarını Türkçe ver ve samimi bir dil kullan.

### Bulunan Tarifler:
{context}
"""

RAG_USER_PROMPT = "{question}"

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", RAG_SYSTEM_PROMPT),
    ("human", RAG_USER_PROMPT),
])


class RAGService:

    @classmethod
    def _get_llm(cls) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
            max_output_tokens=2048,
        )

    @classmethod
    async def ask(cls, question: str, n_results: int = 5) -> dict:
        logger.info("RAG sorgusu başlatıldı: '%s'", question)

        relevant_docs = await VectorStoreService.search(question, n_results=n_results)

        if not relevant_docs:
            logger.warning("Vektör aramasında sonuç bulunamadı: '%s'", question)
            return {
                "answer": "Üzgünüm, bu konuda veritabanımda yeterli tarif bulamadım. "
                          "Lütfen farklı bir soru sormayı deneyin.",
                "sources": [],
            }

        context = "\n\n---\n\n".join(doc["text"] for doc in relevant_docs)

        llm = cls._get_llm()
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
