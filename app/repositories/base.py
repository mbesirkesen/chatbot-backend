from typing import TypeVar, Generic
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic base repository for CRUD operations.
    
    Tüm repository'ler bu sınıftan türetilmelidir.
    Ortak CRUD operasyonlarını sağlar.
    """

    def __init__(self, db: AsyncSession, model: type[T]):
        self._db = db
        self._model = model

    async def get_by_id(self, id: UUID) -> T | None:
        """ID ile entity getirir."""
        result = await self._db.execute(
            select(self._model).where(self._model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[T]:
        """Tüm entity'leri sayfalı olarak getirir."""
        result = await self._db.execute(
            select(self._model)
            .order_by(self._model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, data) -> T:
        """Yeni entity oluşturur."""
        entity = self._model(**data.model_dump())
        self._db.add(entity)
        await self._db.flush()
        await self._db.refresh(entity)
        logger.info(
            "%s oluşturuldu: id=%s",
            self._model.__name__,
            entity.id,
        )
        return entity

    async def update(self, id: UUID, data) -> T | None:
        """Entity günceller."""
        entity = await self.get_by_id(id)
        if not entity:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entity, field, value)

        await self._db.flush()
        await self._db.refresh(entity)
        logger.info(
            "%s güncellendi: id=%s",
            self._model.__name__,
            id,
        )
        return entity

    async def delete(self, id: UUID) -> bool:
        """Entity siler."""
        entity = await self.get_by_id(id)
        if not entity:
            return False

        await self._db.delete(entity)
        await self._db.flush()
        logger.info(
            "%s silindi: id=%s",
            self._model.__name__,
            id,
        )
        return True
