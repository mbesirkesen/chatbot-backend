import uuid
from datetime import datetime

from sqlalchemy import String, Text, Float, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    ingredients: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    cuisine: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cook_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def to_document_text(self) -> str:
        """Vektör veritabanına gönderilecek metin temsilini oluşturur."""
        ingredients_text = ", ".join(self.ingredients)
        return (
            f"Tarif: {self.title}\n"
            f"Açıklama: {self.description or ''}\n"
            f"Malzemeler: {ingredients_text}\n"
            f"Yapılış: {self.instructions}\n"
            f"Mutfak: {self.cuisine or 'Belirtilmemiş'}\n"
            f"Kategori: {self.category or 'Belirtilmemiş'}\n"
            f"Zorluk: {self.difficulty or 'Belirtilmemiş'}"
        )

    def __repr__(self) -> str:
        return f"<Recipe(id={self.id}, title='{self.title}')>"
