from uuid import UUID


class AppException(Exception):
    """Uygulama genelinde kullanılan temel exception sınıfı."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class RecipeNotFoundError(AppException):
    """Tarif bulunamadığında fırlatılır."""

    def __init__(self, recipe_id: UUID | str):
        super().__init__(
            status_code=404,
            detail=f"Tarif bulunamadı: {recipe_id}"
        )


class VectorStoreError(AppException):
    """Vektör veritabanı işlemlerinde hata oluştuğunda fırlatılır."""

    def __init__(self, detail: str = "Vektör veritabanı hatası"):
        super().__init__(status_code=503, detail=detail)


class RAGServiceError(AppException):
    """RAG servisi hata verdiğinde fırlatılır."""

    def __init__(self, detail: str = "Yapay zeka servisi şu anda kullanılamıyor"):
        super().__init__(status_code=503, detail=detail)
