from .common import *

from app.models.ingredient_model import RecipeIngredient
from app.models.instruction_model import InstructionModel
from app.models.recipe_model import RecipeModel, UpdateRecipeModel

router = APIRouter()

@router.post("/", response_description="Add new recipe")
async def create_recipe(request: Request, recipe: RecipeModel = Body(...)):
    recipe = jsonable_encoder(recipe)
    new_recipe = await request.app.mongodb["recipes"].insert_one(recipe)
    created_recipe = await request.app.mongodb["recipes"].find_one(
        {"_id": new_recipe.inserted_id}
    )

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_recipe)

@router.get("/", response_description="List all recipes")
async def list_recipes(request: Request):
    recipes = []
    for doc in await request.app.mongodb["recipes"].find().to_list(length=100):
        recipes.append(doc)
    return recipes

@router.get("/{id}", response_description="Get a single recipe given its id")
async def show_recipe(id: str, request: Request):
    if (recipe := await request.app.mongodb["recipes"].find_one({"_id": id})) is not None:
        return recipe

    raise HTTPException(status_code=404, detail=f"Recipe {id} not found")

@router.put("/{id}", response_description="Update a recipe")
async def update_recipe(id: str, request: Request, recipe: UpdateRecipeModel = Body(...)):
    recipe = {k: v for k, v in recipe.model_dump().items() if v is not None}

    if len(recipe) >= 1:
        update_result = await request.app.mongodb["recipes"].update_one(
            {"_id": id}, {"$set": recipe}
        )

        if update_result.modified_count == 1:
            if (
                updated_recipe := await request.app.mongodb["recipes"].find_one({"_id": id})
            ) is not None:
                return updated_recipe

    if (
        existing_recipe := await request.app.mongodb["recipes"].find_one({"_id": id})
    ) is not None:
        return existing_recipe

    raise HTTPException(status_code=404, detail=f"Recipe {id} not found")

@router.delete("/{id}", response_description="Delete Recipe")
async def delete_recipe(id: str, request: Request):
    delete_result = await request.app.mongodb["recipes"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)
    
    raise HTTPException(status_code=404, detail=f"Recipe {id} not found")