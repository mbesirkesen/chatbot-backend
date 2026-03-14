import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RecipeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, examples=["Mercimek Çorbası"])
    description: str | None = Field(None, examples=["Klasik Türk mutfağı mercimek çorbası"])
    ingredients: list[str] = Field(..., min_length=1, examples=[["kırmızı mercimek", "soğan", "havuç", "patates"]])
    instructions: str = Field(..., min_length=1)
    cuisine: str | None = Field(None, max_length=100, examples=["Türk"])
    category: str | None = Field(None, max_length=100, examples=["Çorba"])
    prep_time_minutes: int | None = Field(None, ge=0)
    cook_time_minutes: int | None = Field(None, ge=0)
    servings: int | None = Field(None, ge=1)
    difficulty: str | None = Field(None, examples=["Kolay"])
    rating: float | None = Field(None, ge=0.0, le=5.0)


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    ingredients: list[str] | None = Field(None, min_length=1)
    instructions: str | None = Field(None, min_length=1)
    cuisine: str | None = Field(None, max_length=100)
    category: str | None = Field(None, max_length=100)
    prep_time_minutes: int | None = Field(None, ge=0)
    cook_time_minutes: int | None = Field(None, ge=0)
    servings: int | None = Field(None, ge=1)
    difficulty: str | None = None
    rating: float | None = Field(None, ge=0.0, le=5.0)


class RecipeResponse(RecipeBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecipeSearchQuery(BaseModel):
    query: str = Field(..., min_length=1, examples=["tavuklu yemekler"])
    ingredients: list[str] | None = Field(None, examples=[["tavuk", "pirinç"]])
    cuisine: str | None = None
    category: str | None = None
    limit: int = Field(10, ge=1, le=50)


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, examples=["Elimde tavuk ve pirinç var, ne yapabilirim?"])
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    answer: str
    sources: list[RecipeResponse] = []
