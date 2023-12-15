import random
from .common import *
from app.models.ingredient_model import RecipeIngredient
from app.models.instruction_model import InstructionModel
from app.models.recipe_model import RecipeModel, UpdateRecipeModel
from app.models.user_model import UserModel
from fastapi import Form, UploadFile, File
from datetime import datetime
from google.cloud import storage
from pymongo import ASCENDING, DESCENDING
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

def create_flexible_regex(search_term):
    pattern = '.*'.join(map(re.escape, search_term))  # This will create a pattern with .* between each character
    return {'$regex': pattern, '$options': 'i'}

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

  
@router.get("/magic", response_description="Get recipes with filtering, sorting, and pagination")
async def get_magic_recipes(
    start: Optional[int] = 0,
    size: Optional[int] = 10,
    sort_by: Optional[str] = None,
    order: Optional[bool] = True,
    min_cooking_time: Optional[int] = None,
    max_cooking_time: Optional[int] = None,
    min_difficulty: Optional[int] = None,
    max_difficulty: Optional[int] = None,
    min_energy: Optional[int] = None,
    max_energy: Optional[int] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    search: Optional[str] = None,
    feedType: Optional[str] = None,  # New parameter
    db: AsyncIOMotorClient = Depends(get_database),
    current_user: UserModel = Depends(get_current_user)
):
    query = {}

    if min_cooking_time is not None:
        query["cooking_time"] = {"$gte": min_cooking_time}
    if max_cooking_time is not None:
        query.setdefault("cooking_time", {})["$lte"] = max_cooking_time
    if min_difficulty is not None:
        query["difficulty"] = {"$gte": min_difficulty}
    if max_difficulty is not None:
        query.setdefault("difficulty", {})["$lte"] = max_difficulty
    if min_energy is not None:
        query["energy"] = {"$gte": min_energy}
    if max_energy is not None:
        query.setdefault("energy", {})["$lte"] = max_energy
    if min_rating is not None:
        query["average_rating"] = {"$gte": min_rating}
    if max_rating is not None:
        query.setdefault("average_rating", {})["$lte"] = max_rating

    # Flexible search functionality
    if search:
        regex_search = create_flexible_regex(search)
        query["$or"] = [
            {"name": regex_search},
            {"ingredients.name": regex_search},
            {"username": regex_search}
        ]

    # Modify existing query based on feedType
    if feedType and current_user:
        if feedType not in ['foryou', 'following']:
            raise HTTPException(status_code=400, detail="Invalid feed type")

        user = await db["users"].find_one({"_id": current_user["user_id"]})
        following = user.get("following", [])
        
        if feedType == 'following':
            # Filter recipes from followed users, while keeping other filters
            query["username"] = {"$in": following}
        
        elif feedType == 'foryou':
            # Filter public recipes not from followed users and not from the current user
            foryou_conditions = [{"is_public": True}, {"username": {"$nin": following + [current_user["username"]]} }]
            query = {"$and": [query, *foryou_conditions]} if query else {"$and": foryou_conditions}

    # Sorting
    if sort_by:
        sort_order = ASCENDING if order else DESCENDING
        # Add a secondary sort key for consistency, e.g., '_id'
        sort_params = [(sort_by, sort_order), ('_id', ASCENDING)]
    else:
        sort_params = None  # No sorting

    # Pagination
    total_recipes = await db["recipes"].count_documents(query)

    if start >= total_recipes:
        raise HTTPException(status_code=400, detail="Start index out of range.")

    if start + size > total_recipes:
        size = total_recipes - start

    cursor = db["recipes"].find(query)
    if sort_params:
        cursor = cursor.sort(sort_params)
    recipes = await cursor.skip(start).limit(size).to_list(length=size)

    return recipes
  
  
@router.get("/similar/{id}", response_description="List similar recipes")
async def list_similar_recipes(id: str, db: AsyncIOMotorClient = Depends(get_database), current_user: Optional[Dict[str, str]] = Depends(get_current_user)):
    username = current_user["username"] if current_user else None

    if username:
        # Retrieve the current user from the database
        user = await db["users"].find_one({"_id": current_user["user_id"]})

    # Retrieve the current recipe from the database
    recipe = await db["recipes"].find_one({"_id": id})

    if recipe is None:
        raise HTTPException(status_code=404, detail=f"Recipe {id} not found")

    similar_recipes = []
    query = {"$or": [{"is_public": True}]}

    if username:
        query["$or"].append({"username": username})
        query["$or"].append({"$and": [{"is_public": False}, {"username": {"$in": user.get("following", [])}}]})

    # Retrieve all similar recipes
    similar_recipes = await db["recipes"].aggregate([{"$sample": {"size": 6}}]).to_list(length=6)

    return similar_recipes

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
            recipe_update['main_image'] = image_urls

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

async def upload_image(file: UploadFile, name):
    storage_client = storage.Client(project=project_name)
    bucket = storage_client.get_bucket(bucket_name)
    point = name.rindex('.')
    fullname = 'recipes/' + name[:point].replace(" ", "_") + '-' + str(time.time_ns()) + name[point:]
    blob = bucket.blob(fullname)
    
    data = await file.read()
    UPLOAD_DIR = Path('')
    save_to = UPLOAD_DIR / file.filename
    with open(save_to, "wb") as f:
        f.write(data)
    blob.upload_from_filename(save_to)
    os.remove(save_to)
    
    return fullname