from functools import wraps

from app.core.logging import logger


def sync_to_vector_store(func):
    """
    Tarif oluşturma/güncelleme sonrası vektör DB'ye senkronize eder.
    
    Bu decorator, service metodlarında kullanılarak DRY prensibine
    uygun şekilde vektör senkronizasyonunu otomatikleştirir.
    
    Kullanım:
        class RecipeService:
            @sync_to_vector_store
            async def create(self, data: RecipeCreate) -> Recipe:
                return await self._repo.create(data)
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        recipe = await func(self, *args, **kwargs)
        if recipe and hasattr(self, "_vector_svc") and self._vector_svc:
            try:
                await self._vector_svc.sync_recipe(recipe)
            except Exception as e:
                logger.error(
                    "Vektör veritabanına senkronizasyon başarısız: %s", e
                )
        return recipe
    return wrapper


def log_operation(operation_name: str):
    """
    Servis operasyonlarını loglar.
    
    Args:
        operation_name: Log mesajında kullanılacak operasyon adı
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            logger.info("%s başlatıldı", operation_name)
            try:
                result = await func(self, *args, **kwargs)
                logger.info("%s tamamlandı", operation_name)
                return result
            except Exception as e:
                logger.error("%s hatası: %s", operation_name, e)
                raise
        return wrapper
    return decorator
