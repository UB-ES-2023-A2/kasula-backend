from enum import Enum
from .common import *

class Unit(str, Enum):
    cup = "cup"
    tbsp = "tbsp"
    tsp = "tsp"
    oz = "oz"
    lb = "lb"
    g = "g"
    kg = "kg"
    ml = "ml"
    l = "l"
    pt = "pt"
    qt = "qt"
    gal = "gal"
    count = "count"


class IngredientModel(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    name: str = Field(...)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "00010203-0405-0607-0809-0a0b0c0d0e0f",
                "name": "Ingredient Name"
            }
        }


class RecipeIngredient(IngredientModel):
    quantity: float = Field(1)
    unit: Unit = Field(...)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "00010203-0405-0607-0809-0a0b0c0d0e0f",
                "name": "Ingredient Name",
                "quantity": 1,
                "unit": "cup"
            }
        }

class UpdateIngredientModel(BaseModel):
    name: Optional[str]
    quantity: Optional[float]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Ingredient Name"
            }
        }

class UpdateRecipeIngredientModel(UpdateIngredientModel):
    quantity: Optional[int]
    unit: Optional[Unit]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Ingredient Name",
                "quantity": 1,
                "unit": "cup"
            }
        }