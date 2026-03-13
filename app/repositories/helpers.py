from sqlalchemy import func

from app.models.recipe import Recipe


def build_ingredient_conditions(ingredients: list[str]):
    """
    Malzeme arama koşulları oluşturur.
    
    Verilen malzemelerden herhangi birini içeren tarifleri bulmak için
    SQLAlchemy koşulları döner.
    
    Args:
        ingredients: Aranacak malzeme listesi
        
    Returns:
        SQLAlchemy koşul listesi (OR ile birleştirilecek)
    """
    return [
        Recipe.ingredients.any(func.lower(ing.lower()))
        for ing in ingredients
    ]
