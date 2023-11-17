from .common import *
from .ingredient_model import RecipeIngredient
from .instruction_model import InstructionModel
from typing import List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class RecipeModel(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    name: str = Field("Recipe Name", max_length=50)
    ingredients: List[RecipeIngredient] = Field(...)
    instructions: List[InstructionModel] = Field(...)
    cooking_time: int = Field(default=0)
    difficulty: int = Field(default=0)
    image: Optional[str] = Field(None)
    energy: Optional[int] = Field(None)
    username: Optional[str] = Field(None)
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "00010203-0405-0607-0809-0a0b0c0d0e0f",
                "name": "Recipe Name",
                "ingredients": [
                    {
                        "id": "00010203-0405-0607-0809-0a0b0c0d0e0f",
                        "name": "Ingredient Name",
                        "quantity": 1,
                        "unit": "cup"
                    }
                ],
                "instructions": [
                    {
                        "id": "00010203-0405-0607-0809-0a0b0c0d0e0f",
                        "body": "Recipe Name",
                        "step_number": 1,
                        #"image": "imgurl",
                    }
                ],
                "cooking_time": 1,
                "difficulty": 1,
                "image": "imgurl",
                "energy": 400,
                "user_id": "00010203-0405-0607-0809-0a0b0c0d0e0f",
            }
        }


class UpdateRecipeModel(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    ingredients: Optional[List[RecipeIngredient]] = Field(None)
    instructions: Optional[List[InstructionModel]] = Field(None)
    cooking_time: Optional[int] = Field(None)
    difficulty: Optional[int] = Field(None)
    image: Optional[str] = Field(None)
    energy: Optional[int] = Field(None)
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Recipe Name",
                "ingredients": [
                    {
                        "id": "00010203-0405-0607-0809-0a0b0c0d0e0f",
                        "name": "Ingredient Name",
                        "quantity": 1,
                        "unit": "cup"
                    }
                ],
                "instructions": [
                    {
                        "id": "00010203-0405-0607-0809-0a0b0c0d0e0f",
                        "body": "Recipe Name",
                        "step_number": 1,
                        #"image": "imgurl",
                    }
                ],
                "cooking_time": 1,
                "difficulty": 1,
                "image": "imgurl",
                "energy": 400,
            }
        }