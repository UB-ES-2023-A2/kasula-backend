from .common import *

from app.models.ingredient_model import RecipeIngredient
from app.models.instruction_model import InstructionModel
from app.models.recipe_model import RecipeModel, UpdateRecipeModel
from app.models.user_model import UserModel

import requests
import os


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
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Recipe successfully deleted"})
    
    raise HTTPException(status_code=404, detail=f"Recipe {id} not found")


# Upload recipe image (locally for now)
from fastapi import UploadFile
from pathlib import Path

@router.post("/uploadfile")
async def create_upload_file(file: UploadFile | None = None):
    if not file:
        return {"message": "No upload file sent"}
    else:
        fullname = await upload_image(file, file.filename)
        print("Finished execution")
        print(fullname)
        return {"file_url": f'https://storage.googleapis.com/bucket-kasula_images/{fullname}'}


from google.cloud import storage
import time

project_name = 'kasula'
bucket_name = 'bucket-kasula_images'

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


'''
# OLD, Using Token that expires every hour
GOOGLE_CLOUD_TOKEN = os.getenv("GOOGLE_CLOUD_TOKEN")
def upload_image_old(data, name):
    headers = {
        'Authorization': GOOGLE_CLOUD_TOKEN, # Needs to be refreshed every hour.......
        'Content-Type': 'image/jpeg',
    }
    params = {
        'uploadType': 'media',
        'name': f'recipes/{name}'
    }
    print(headers)
    print(params)
    response = requests.post(
        'https://storage.googleapis.com/upload/storage/v1/b/bucket-kasula_images/o',
        headers=headers,
        params=params,
        data=data)

    return response.json()
'''
