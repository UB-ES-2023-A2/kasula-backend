from .common import *

from app.models.ingredient_model import RecipeIngredient
from app.models.instruction_model import InstructionModel
from app.models.recipe_model import RecipeModel, UpdateRecipeModel
from app.models.user_model import UserModel

router = APIRouter()

def get_database(request: Request):
    return request.app.mongodb

@router.post("/", response_description="Add new recipe")
async def create_recipe(db: AsyncIOMotorClient = Depends(get_database), recipe: RecipeModel = Body(...), current_user: UserModel = Depends(get_current_user)):
    recipe.user_id = current_user["user_id"]
    recipe = jsonable_encoder(recipe)
    new_recipe = await db["recipes"].insert_one(recipe)
    created_recipe = await db["recipes"].find_one({"_id": new_recipe.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_recipe)

@router.get("/", response_description="List all recipes")
async def list_recipes(db: AsyncIOMotorClient = Depends(get_database)):
    recipes = []
    for doc in await db["recipes"].find().to_list(length=100):
        recipes.append(doc)
    return recipes

@router.get("/{id}", response_description="Get a single recipe given its id")
async def show_recipe(id: str, db: AsyncIOMotorClient = Depends(get_database)):
    if (recipe := await db["recipes"].find_one({"_id": id})) is not None:
        return recipe

    raise HTTPException(status_code=404, detail=f"Recipe {id} not found")

@router.put("/{id}", response_description="Update a recipe")
async def update_recipe(id: str, db: AsyncIOMotorClient = Depends(get_database), recipe: UpdateRecipeModel = Body(...), current_user: UserModel = Depends(get_current_user)):
    # Retrieve the existing recipe from the database.
    existing_recipe = await db["recipes"].find_one({"_id": id})
    
    # If no such recipe exists, return a 404 error.
    if existing_recipe is None:
        raise HTTPException(status_code=404, detail=f"Recipe {id} not found")
    
    # Check if the user trying to update the recipe is the one who created it.
    if existing_recipe.get("user_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this recipe")

    # Update the recipe in the database.
    recipe = {k: v for k, v in recipe.model_dump().items() if v is not None}

    if len(recipe) >= 1:
        update_result = await db["recipes"].update_one(
            {"_id": id}, {"$set": recipe}
        )

        if update_result.modified_count == 1:
            if (
                updated_recipe := await db["recipes"].find_one({"_id": id})
            ) is not None:
                return updated_recipe

    if (
        existing_recipe := await db["recipes"].find_one({"_id": id})
    ) is not None:
        return existing_recipe

    raise HTTPException(status_code=404, detail=f"Recipe {id} not found")

@router.delete("/{id}", response_description="Delete Recipe")
async def delete_recipe(id: str, db: AsyncIOMotorClient = Depends(get_database), current_user: UserModel = Depends(get_current_user)):
    # Retrieve the existing recipe from the database.
    existing_recipe = await db["recipes"].find_one({"_id": id})

    # If no such recipe exists, return a 404 error.
    if existing_recipe is None:
        raise HTTPException(status_code=404, detail=f"Recipe {id} not found")

    # Check if the user trying to delete the recipe is the one who created it.
    if existing_recipe.get("user_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this recipe")

    # Delete the recipe from the database.
    delete_result = await db["recipes"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=delete_result.raw_result)
    
    raise HTTPException(status_code=404, detail=f"Recipe {id} not found")