# Yemek Tarifi Chatbot API

Yapay zeka destekli yemek tarifi chatbot backend servisi. RAG (Retrieval-Augmented Generation) mimarisi kullanarak tarifler arasında akıllı arama yapar ve kullanıcı sorularını yanıtlar.

## Teknolojiler

- **Framework**: FastAPI (async)
- **Veritabanı**: PostgreSQL + SQLAlchemy (async)
- **Vektör DB**: ChromaDB
- **LLM**: Google Gemini
- **Embeddings**: Google Generative AI Embeddings

---

## Mimari Genel Bakış

Bu proje **Clean Architecture** prensiplerine uygun katmanlı bir yapı kullanır:

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (Endpoints)                   │
│  HTTP isteklerini alır, yanıt döner. İş mantığı içermez.   │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                            │
│  İş mantığını içerir. Repository ve harici servisler ile   │
│  iletişim kurar.                                            │
├─────────────────────────────────────────────────────────────┤
│                   Repository Layer                          │
│  Veritabanı erişimini soyutlar. CRUD operasyonları.        │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure                            │
│  PostgreSQL, ChromaDB, Gemini API                          │
└─────────────────────────────────────────────────────────────┘
```

**Veri Akışı:**
```
Request → Endpoint → Service → Repository → Database
                  ↘ VectorStore → ChromaDB
                  ↘ RAGService → Gemini API
```

---

## Proje Yapısı

```
app/
├── main.py                      # FastAPI uygulama başlangıcı
├── api/
│   ├── __init__.py
│   ├── dependencies.py          # DI factory fonksiyonları + get_recipe_or_404
│   └── v1/
│       ├── __init__.py
│       ├── router.py            # Tüm endpoint'leri birleştirir
│       └── endpoints/
│           ├── __init__.py
│           ├── chat.py          # POST /chat - RAG sohbet
│           └── recipes.py       # CRUD /recipes
├── core/
│   ├── __init__.py
│   ├── config.py                # Settings sınıfı (.env okur)
│   ├── container.py             # DI container (alternatif)
│   ├── database.py              # AsyncSession, engine
│   ├── logging.py               # Logger yapılandırması
│   ├── exceptions/
│   │   ├── __init__.py
│   │   ├── base.py              # AppException, RecipeNotFoundError
│   │   └── handlers.py          # Exception handler fonksiyonları
│   └── middleware/
│       ├── __init__.py
│       └── logging.py           # RequestLoggingMiddleware
├── domain/
│   ├── __init__.py
│   └── interfaces/
│       ├── __init__.py
│       ├── repository.py        # IRepository, IRecipeRepository protokolleri
│       └── services.py          # IVectorStore, IRAGService protokolleri
├── models/
│   ├── __init__.py
│   └── recipe.py                # SQLAlchemy Recipe modeli
├── schemas/
│   ├── __init__.py
│   └── recipe.py                # Pydantic DTO'ları (Create, Update, Response)
├── repositories/
│   ├── __init__.py
│   ├── base.py                  # BaseRepository (generic CRUD)
│   ├── helpers.py               # build_ingredient_conditions
│   └── recipe_repository.py     # RecipeRepository
└── services/
    ├── __init__.py
    ├── decorators.py            # @sync_to_vector_store
    ├── recipe_service.py        # RecipeService
    ├── rag_service.py           # RAGService
    └── vector_store.py          # VectorStoreService
```

---

## AI Agent / Geliştirici Rehberi

> **Bu bölüm, kod yapısını bozmadan geliştirme yapabilmek için kritik kuralları içerir.**

### Katman Sorumlulukları

| Katman | Dosya Konumu | Ne Yapar | Ne Yapmaz |
|--------|--------------|----------|-----------|
| **Endpoint** | `api/v1/endpoints/` | HTTP request/response, validation | İş mantığı, DB erişimi |
| **Service** | `services/` | İş mantığı, orchestration | Doğrudan SQL, HTTP |
| **Repository** | `repositories/` | DB erişimi, CRUD | İş mantığı |
| **Schema** | `schemas/` | DTO tanımları | İş mantığı |
| **Model** | `models/` | ORM tanımları | İş mantığı |

### Yeni Özellik Eklerken Sıra

1. `models/` → SQLAlchemy model
2. `schemas/` → Pydantic DTO'lar (Create, Update, Response)
3. `repositories/` → Repository sınıfı (BaseRepository'den miras)
4. `services/` → Service sınıfı (iş mantığı)
5. `api/dependencies.py` → DI factory fonksiyonları
6. `api/v1/endpoints/` → Endpoint dosyası
7. `api/v1/router.py` → Router'a include et

### Referans Dosyalar (Örnek Al)

Yeni kod yazarken bu dosyaları örnek al:

| Yeni Oluşturacağın | Örnek Al |
|--------------------|----------|
| Yeni endpoint | `app/api/v1/endpoints/recipes.py` |
| Yeni service | `app/services/recipe_service.py` |
| Yeni repository | `app/repositories/recipe_repository.py` |
| Yeni model | `app/models/recipe.py` |
| Yeni schema | `app/schemas/recipe.py` |
| Yeni exception | `app/core/exceptions/base.py` |
| Yeni dependency | `app/api/dependencies.py` |

---

## Kod Yazım Kuralları

### 1. İsimlendirme (Naming Conventions)

```python
# Dosya isimleri: snake_case
recipe_service.py
user_repository.py

# Sınıf isimleri: PascalCase
class RecipeService:
class UserRepository:

# Fonksiyon/metod: snake_case
async def get_by_id(self, recipe_id: UUID):
async def create_recipe(data: RecipeCreate):

# Değişkenler: snake_case
recipe_data = ...
user_list = ...

# Sabitler: SCREAMING_SNAKE_CASE
DEFAULT_LIMIT = 20
MAX_RESULTS = 100

# Private: tek underscore prefix
self._repo = repo
self._db = db
```

### 2. Import Sıralaması

```python
# 1. Standart kütüphane
from uuid import UUID
from datetime import datetime

# 2. Üçüncü parti
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Yerel - core
from app.core.logging import logger
from app.core.database import get_db

# 4. Yerel - domain/interfaces
from app.domain.interfaces import IVectorStore

# 5. Yerel - models/schemas
from app.models.recipe import Recipe
from app.schemas.recipe import RecipeCreate

# 6. Yerel - repositories/services
from app.repositories import RecipeRepository
from app.services import RecipeService
```

### 3. Type Hints (Zorunlu)

```python
# Tüm fonksiyonlarda parametre ve dönüş tipi belirt
async def get_by_id(self, recipe_id: UUID) -> Recipe | None:
    ...

async def get_all(self, skip: int = 0, limit: int = 20) -> list[Recipe]:
    ...

# Optional için | None kullan (Union değil)
def __init__(self, vector_svc: IVectorStore | None = None):
    ...
```

### 4. Docstring Formatı

```python
async def search(
    self,
    query: str | None = None,
    ingredients: list[str] | None = None,
    limit: int = 10,
) -> list[Recipe]:
    """
    Çoklu kriterlere göre tarif arar.
    
    Args:
        query: Başlık/açıklamada aranacak metin
        ingredients: Aranacak malzeme listesi
        limit: Maksimum sonuç sayısı
        
    Returns:
        Eşleşen tariflerin listesi
    """
```

---

## Pattern'lar ve Örnekler

### Endpoint Yazımı

```python
# app/api/v1/endpoints/recipes.py - DOĞRU ÖRNEK

@router.post("/", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    data: RecipeCreate,
    service: RecipeService = Depends(get_recipe_service),
):
    """Yeni tarif oluşturur."""
    return await service.create(data)


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe: Recipe = Depends(get_recipe_or_404),  # 404 kontrolü dependency'de
):
    """ID ile tarif getirir."""
    return recipe
```

**Endpoint Kuralları:**
- Service'i `Depends()` ile al
- İş mantığı yazma, `service.method()` çağır
- 404 kontrolü için `get_X_or_404` dependency kullan
- Response model belirt
- Kısa docstring ekle

### Service Yazımı

```python
# app/services/recipe_service.py - DOĞRU ÖRNEK

class RecipeService:
    def __init__(
        self,
        repo: RecipeRepository,
        vector_svc: IVectorStore | None = None,
    ):
        self._repo = repo
        self._vector_svc = vector_svc

    @sync_to_vector_store  # Decorator ile vektör sync
    async def create(self, data: RecipeCreate) -> Recipe:
        recipe = await self._repo.create(data)
        logger.info("Yeni tarif oluşturuldu: %s (id=%s)", recipe.title, recipe.id)
        return recipe

    async def get_by_id(self, recipe_id: UUID) -> Recipe | None:
        return await self._repo.get_by_id(recipe_id)
```

**Service Kuralları:**
- Constructor'da dependency'leri al (DI)
- Repository metodlarını çağır
- İş mantığını burada yaz
- Loglama burada yap
- Vektör sync için `@sync_to_vector_store` decorator kullan

### Repository Yazımı

```python
# app/repositories/recipe_repository.py - DOĞRU ÖRNEK

class RecipeRepository(BaseRepository[Recipe]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Recipe)

    async def search_by_title(self, query: str, limit: int = 10) -> list[Recipe]:
        result = await self._db.execute(
            select(Recipe)
            .where(func.lower(Recipe.title).contains(query.lower()))
            .limit(limit)
        )
        return list(result.scalars().all())
```

**Repository Kuralları:**
- `BaseRepository[Model]`'den miras al
- Sadece veritabanı işlemleri yap
- SQLAlchemy `select()` kullan
- Sonuçları `list()` ile dön

### Dependency Yazımı

```python
# app/api/dependencies.py - DOĞRU ÖRNEK

def get_recipe_repository(
    db: AsyncSession = Depends(get_db),
) -> RecipeRepository:
    return RecipeRepository(db)


def get_recipe_service(
    repo: RecipeRepository = Depends(get_recipe_repository),
    vector_svc: VectorStoreService = Depends(get_vector_service),
) -> RecipeService:
    return RecipeService(repo, vector_svc)


async def get_recipe_or_404(
    recipe_id: UUID,
    service: RecipeService = Depends(get_recipe_service),
) -> Recipe:
    """Tarifi getirir, bulunamazsa 404 fırlatır."""
    recipe = await service.get_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Tarif bulunamadı")
    return recipe
```

---

## Yapılmaması Gerekenler (Anti-Patterns)

```python
# YANLIŞ: Endpoint'te iş mantığı
@router.post("/")
async def create_recipe(data: RecipeCreate, db: AsyncSession = Depends(get_db)):
    recipe = Recipe(**data.model_dump())
    db.add(recipe)
    await db.flush()
    await VectorStoreService.add_recipe(...)  # YANLIŞ!
    return recipe

# DOĞRU: Service'e delege et
@router.post("/")
async def create_recipe(
    data: RecipeCreate,
    service: RecipeService = Depends(get_recipe_service)
):
    return await service.create(data)
```

```python
# YANLIŞ: Service'te doğrudan SQL
class RecipeService:
    async def get_all(self, db: AsyncSession):
        result = await db.execute(select(Recipe))  # YANLIŞ!
        return result.scalars().all()

# DOĞRU: Repository kullan
class RecipeService:
    async def get_all(self) -> list[Recipe]:
        return await self._repo.get_all()
```

```python
# YANLIŞ: Tekrarlayan 404 kontrolü
@router.get("/{recipe_id}")
async def get_recipe(recipe_id: UUID, service: RecipeService = Depends(...)):
    recipe = await service.get_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Tarif bulunamadı")
    return recipe

# DOĞRU: Dependency kullan
@router.get("/{recipe_id}")
async def get_recipe(recipe: Recipe = Depends(get_recipe_or_404)):
    return recipe
```

```python
# YANLIŞ: Static method service
class RecipeService:
    @staticmethod
    async def create(db, data):  # YANLIŞ!
        ...

# DOĞRU: Instance method + DI
class RecipeService:
    def __init__(self, repo: RecipeRepository):
        self._repo = repo
    
    async def create(self, data: RecipeCreate) -> Recipe:
        ...
```

---

## Yeni Özellik Ekleme Checklist

Örnek: "Kullanıcı yorumları" özelliği eklemek

- [ ] `app/models/comment.py` → Comment SQLAlchemy modeli
- [ ] `app/schemas/comment.py` → CommentCreate, CommentResponse
- [ ] `app/repositories/comment_repository.py` → CommentRepository(BaseRepository)
- [ ] `app/services/comment_service.py` → CommentService
- [ ] `app/api/dependencies.py` → get_comment_repository, get_comment_service
- [ ] `app/api/v1/endpoints/comments.py` → CRUD endpoint'leri
- [ ] `app/api/v1/router.py` → `api_router.include_router(comments.router)`
- [ ] Import'ları `__init__.py` dosyalarına ekle

---

## Mevcut API Endpoint'leri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/` | Sağlık kontrolü |
| GET | `/health` | Sağlık kontrolü |
| POST | `/api/v1/recipes/` | Yeni tarif oluştur |
| GET | `/api/v1/recipes/` | Tarifleri listele |
| GET | `/api/v1/recipes/{id}` | Tarif detayı |
| PUT | `/api/v1/recipes/{id}` | Tarif güncelle |
| DELETE | `/api/v1/recipes/{id}` | Tarif sil |
| POST | `/api/v1/recipes/search` | Tarif ara |
| POST | `/api/v1/chat/` | RAG sohbet |

---

## Kurulum

```bash
# Virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Bağımlılıklar
pip install -r requirements.txt

# Ortam değişkenleri
cp .env.example .env
# .env dosyasını düzenle (DATABASE_URL, GEMINI_API_KEY zorunlu)

# Çalıştır
uvicorn app.main:app --reload
```

---

## Konfigürasyon

Değerler `.env` dosyasından okunur:

| Değişken | Zorunlu | Varsayılan | Açıklama |
|----------|---------|------------|----------|
| DATABASE_URL | Evet | - | PostgreSQL bağlantı URL'i |
| GEMINI_API_KEY | Evet | - | Google Gemini API anahtarı |
| DEBUG | Hayır | False | Debug modu |
| LOG_LEVEL | Hayır | INFO | Log seviyesi |
| GEMINI_MODEL | Hayır | gemini-2.0-flash | Gemini model adı |
| CHROMA_PERSIST_DIR | Hayır | ./chroma_data | ChromaDB dizini |
| CHROMA_COLLECTION_NAME | Hayır | recipes | ChromaDB koleksiyon adı |
| EMBEDDING_MODEL | Hayır | models/embedding-001 | Embedding modeli |

---

## API Dokümantasyonu

Uygulama çalışırken:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
