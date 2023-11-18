from .common import *
from app.models.ingredient_model import RecipeIngredient
from app.models.instruction_model import InstructionModel
from app.models.recipe_model import RecipeModel, UpdateRecipeModel
from app.models.user_model import UserModel
from fastapi import Form, UploadFile
from datetime import datetime
from google.cloud import storage
import time

project_name = 'kasula'
bucket_name = 'bucket-kasula_images'
import json
import requests
import os

router = APIRouter()

def get_database(request: Request):
    return request.app.mongodb

@router.post("/", response_description="Add new recipe")
async def create_recipe(db: AsyncIOMotorClient = Depends(get_database), recipe: str = Form(...), file: UploadFile | None = None, current_user: UserModel = Depends(get_current_user)):
    recipe_dict = json.loads(recipe)  # Deserializar la cadena JSON en un diccionario
    recipe_model = RecipeModel(**recipe_dict)
    recipe_model.user_id = current_user["user_id"]

    if not file:
        recipe_model.image = 'None'
    else:
        fullname = await upload_image(file, file.filename)
        recipe_model.image = f'https://storage.googleapis.com/bucket-kasula_images/{fullname}'  # Usar f-string correctamente

    recipe_dict = jsonable_encoder(recipe_model)

    new_recipe = await db["recipes"].insert_one(recipe_dict)
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

    # Convert UpdateRecipeModel to a dictionary and update fields if not None
    recipe_dict = {k: v for k, v in recipe.dict().items() if v is not None}

    # Set updated_at to current datetime
    recipe_dict['updated_at'] = datetime.utcnow()

    if len(recipe_dict) >= 1:
        update_result = await db["recipes"].update_one(
            {"_id": id}, {"$set": recipe_dict}
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
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Recipe successfully deleted"})
    
    raise HTTPException(status_code=404, detail=f"Recipe {id} not found")

@router.get("/user/{username}", response_description="List all recipes by a specific username")
async def list_recipes_by_username(username: str, db: AsyncIOMotorClient = Depends(get_database)):
    # Find the target user by username
    target_user = await db["users"].find_one({"username": username})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Use the user_id of the found user to query recipes
    recipes = []
    for doc in await db["recipes"].find({"user_id": target_user["_id"]}).to_list(length=100):
        recipes.append(doc)
    return recipes

async def upload_image(file : UploadFile, name):
    storage_client = storage.Client(project=project_name)
    bucket = storage_client.get_bucket(bucket_name)
    point = name.rindex('.')
    fullname = 'recipes/' + name[:point] + '-' + str(time.time_ns()) + name[point:]
    blob = bucket.blob(fullname)
    
    data = await file.read()
    # Sembla que hauré de guardar temporalment el fitxer perquè el UploadFile no me'l deixa pujar directament
    UPLOAD_DIR = Path('')
    save_to = UPLOAD_DIR / file.filename
    with open(save_to, "wb") as f:
        f.write(data)
    blob.upload_from_filename(save_to)
    os.remove(save_to)
    
    return fullname
