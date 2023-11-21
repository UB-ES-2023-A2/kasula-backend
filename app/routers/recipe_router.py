from .common import *
from app.models.ingredient_model import RecipeIngredient
from app.models.instruction_model import InstructionModel
from app.models.recipe_model import RecipeModel, UpdateRecipeModel
from app.models.user_model import UserModel
from fastapi import Form, UploadFile, File
from datetime import datetime
from google.cloud import storage
import time
from pathlib import Path
from typing import List, Optional, Dict

project_name = 'kasula'
bucket_name = 'bucket-kasula_images'
import json
import requests
import os

router = APIRouter()

def get_database(request: Request):
    return request.app.mongodb

@router.post("/", response_description="Add new recipe")
async def create_recipe(db: AsyncIOMotorClient = Depends(get_database), recipe: str = Form(...), files: List[UploadFile] = File(None), current_user: UserModel = Depends(get_current_user)):
    # Retrieve the current user from the database
    user = await db["users"].find_one({"_id": current_user["user_id"]})

    if user is None:
        raise HTTPException(status_code=404, detail=f"User not found")

    # Get the value of the "is_private" key for the current user
    is_private = user.get("is_private", False)

    recipe_dict = json.loads(recipe)  # Deserialize the JSON string into a dictionary
    recipe_model = RecipeModel(**recipe_dict)
    recipe_model.username = user["username"]

    # Set user_id to the current user's ID
    recipe_model.user_id = user["_id"]

    recipe_model.is_public = not is_private

    recipe_model.average_rating = 0.0

    if not files:
        recipe_model.main_image = None
        recipe_model.images = []
    else:
        image_urls = []
        for i, file in enumerate(files):
            fullname = await upload_image(file, file.filename)
            image_url = f'https://storage.googleapis.com/bucket-kasula_images/{fullname}'
            if i == 0:
                recipe_model.main_image = image_url
            else:
                image_urls.append(image_url)

        recipe_model.images = image_urls  # Set the images field with the list of URLs

    recipe_dict = jsonable_encoder(recipe_model)
    new_recipe = await db["recipes"].insert_one(recipe_dict)
    created_recipe = await db["recipes"].find_one({"_id": new_recipe.inserted_id})

    if created_recipe is None:
        raise HTTPException(status_code=404, detail=f"Recipe could not be created")

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_recipe)


@router.get("/", response_description="List all recipes")
async def list_recipes(db: AsyncIOMotorClient = Depends(get_database), current_user: Optional[Dict[str, str]] = Depends(get_current_user)):
    username = current_user["username"] if current_user else None

    if username:
        # Retrieve the current user from the database
        user = await db["users"].find_one({"_id": current_user["user_id"]})

    recipes = []
    query = {"$or": [{"is_public": True}]}
    if username:
        query["$or"].append({"username": username})
        query["$or"].append({"$and": [{"is_public": False}, {"username": {"$in": user.get("following", [])}}]})

    async for doc in db["recipes"].find(query).limit(100):
        recipes.append(doc)

    if not recipes:
        return []

    return recipes

@router.get("/{id}", response_description="Get a single recipe given its id")
async def show_recipe(id: str, db: AsyncIOMotorClient = Depends(get_database), current_user: Optional[Dict[str, str]] = Depends(get_current_user)):
    recipe = await db["recipes"].find_one({"_id": id})

    user_id = current_user["user_id"] if current_user else None

    if user_id:
        # Retrieve the current user from the database
        user = await db["users"].find_one({"_id": current_user["user_id"]})

    if recipe is not None:
        if recipe.get("is_public", False):
            return recipe
        elif user_id:
            if recipe.get("user_id") == user_id:
                return recipe
            elif recipe.get("username") in user.get("following", []):
                return recipe
        raise HTTPException(status_code=403, detail=f"The given recipe is not public")
    else:
        raise HTTPException(status_code=404, detail=f"Recipe {id} not found")


@router.put("/{id}", response_description="Update a recipe")
async def update_recipe(
    id: str, 
    db: AsyncIOMotorClient = Depends(get_database), 
    recipe: Optional[str] = Form(None),  # Make the recipe data optional
    files: List[UploadFile] = File(None),  # Accept multiple files
    current_user: UserModel = Depends(get_current_user)
):
    # Retrieve the existing recipe
    existing_recipe = await db["recipes"].find_one({"_id": id})
    if existing_recipe is None:
        raise HTTPException(status_code=404, detail=f"Recipe {id} not found")

    # Authorization check
    if existing_recipe.get("username") != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this recipe")

    recipe_update = {}

    # Parse recipe data if provided
    if recipe:
        recipe_data = json.loads(recipe)
        recipe_model = UpdateRecipeModel(**recipe_data)
        recipe_update = {k: v for k, v in recipe_model.dict().items() if v is not None}

    # Image processing and uploading
    if files:
        image_urls = []
        for file in files:
            fullname = await upload_image(file, file.filename)
            image_url = f'https://storage.googleapis.com/bucket-kasula_images/{fullname}'
            image_urls.append(image_url)

        if image_urls:
            existing_images = existing_recipe.get('images', [])
            recipe_update['images'] = existing_images + image_urls

    # Update logic
    if recipe_update:
        recipe_update['updated_at'] = datetime.utcnow()
        update_result = await db["recipes"].update_one(
            {"_id": id}, {"$set": recipe_update}
        )

        if update_result.modified_count == 1:
            if (
                updated_recipe := await db["recipes"].find_one({"_id": id})
            ) is not None:
                return updated_recipe

    # Return existing recipe if no updates were made
    if (
        existing_recipe := await db["recipes"].find_one({"_id": id})
    ) is not None:
        return existing_recipe

    raise HTTPException(status_code=404, detail=f"Recipe {id} not found")

@router.delete("/{id}", response_description="Delete Recipe")
async def delete_recipe(id: str, db: AsyncIOMotorClient = Depends(get_database), current_user: UserModel = Depends(get_current_user)):
    # Retrieve the existing recipe from the database.
    existing_recipe = await db["recipes"].find_one({"_id": id})

    user = await db["users"].find_one({"_id": current_user["user_id"]})

    # If no such recipe exists, return a 404 error.
    if existing_recipe is None:
        raise HTTPException(status_code=404, detail=f"Recipe {id} not found")

    # Check if the user trying to delete the recipe is the one who created it.
    if existing_recipe.get("username") != user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this recipe")

    # Delete the recipe from the database.
    delete_result = await db["recipes"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Recipe successfully deleted"})
    
    raise HTTPException(status_code=404, detail=f"Recipe {id} not found")

@router.get("/user/{username}", response_description="List all recipes by a specific username")
async def list_recipes_by_username(username: str, db: AsyncIOMotorClient = Depends(get_database), current_user: UserModel = Depends(get_current_user)):
    # Find the target user by username
    target_user = await db["users"].find_one({"username": username})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = current_user["user_id"] if current_user else None

    if user_id:
        user = await db["users"].find_one({"_id": user_id})
    else:
        user = None

    recipes = []
    for doc in await db["recipes"].find({"username": target_user["username"]}).to_list(length=1000):
        if doc.get("is_public"):
            recipes.append(doc)
        elif user:
            if doc.get("username") == user["username"]:
                recipes.append(doc)
    
    if not recipes:
        return []
    
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
