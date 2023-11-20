from .common import *
from app.models.collection_model import CollectionModel, UpdateCollectionModel
from app.models.user_model import UserModel

router = APIRouter()

def get_database(request: Request):
    return request.app.mongodb

@router.post("/", response_description="Create a new collection")
async def create_collection(collection: CollectionModel = Body(...), current_user: UserModel = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    collection.user_id = str(current_user["user_id"])

    # Retrieve the current user from the database
    user = await db["users"].find_one({"_id": current_user["user_id"]})

    collection.username = user["username"]

    new_collection = await db["collections"].insert_one(jsonable_encoder(collection))
    created_collection = await db["collections"].find_one({"_id": new_collection.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_collection)

@router.delete("/{collection_id}", response_description="Delete a collection")
async def delete_collection(collection_id: str, current_user: UserModel = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    collection = await db["collections"].find_one({"_id": collection_id})
    if collection and collection["user_id"] == str(current_user["user_id"]):
        await db["collections"].delete_one({"_id": collection_id})
        return {"message": "Collection deleted"}
    else:
        raise HTTPException(status_code=404, detail="Collection not found or access denied")

@router.put("/{collection_id}", response_description="Update a collection")
async def update_collection(collection_id: str, update_data: UpdateCollectionModel = Body(...), current_user: UserModel = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    collection = await db["collections"].find_one({"_id": collection_id})
    if collection and collection["user_id"] == str(current_user["user_id"]):
        await db["collections"].update_one({"_id": collection_id}, {"$set": update_data.dict(exclude_unset=True)})
        updated_collection = await db["collections"].find_one({"_id": collection_id})
        return updated_collection
    else:
        raise HTTPException(status_code=404, detail="Collection not found or access denied")

@router.put("/{collection_id}/add_recipe/{recipe_id}", response_description="Add a recipe to a collection")
async def add_recipe_to_collection(collection_id: str, recipe_id: str, current_user: UserModel = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    collection = await db["collections"].find_one({"_id": collection_id})
    if collection and collection["user_id"] == str(current_user["user_id"]):
        await db["collections"].update_one({"_id": collection_id}, {"$addToSet": {"recipe_ids": recipe_id}})
        updated_collection = await db["collections"].find_one({"_id": collection_id})
        return updated_collection
    else:
        raise HTTPException(status_code=404, detail="Collection not found or access denied")

@router.put("/{collection_id}/remove_recipe/{recipe_id}", response_description="Remove a recipe from a collection")
async def remove_recipe_from_collection(collection_id: str, recipe_id: str, current_user: UserModel = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    collection = await db["collections"].find_one({"_id": collection_id})
    if collection and collection["user_id"] == str(current_user["user_id"]):
        await db["collections"].update_one({"_id": collection_id}, {"$pull": {"recipe_ids": recipe_id}})
        updated_collection = await db["collections"].find_one({"_id": collection_id})
        return updated_collection
    else:
        raise HTTPException(status_code=404, detail="Collection not found or access denied")

@router.get("/user/{username}", response_description="List all collections of a user")
async def list_collections_by_user(username: str, db: AsyncIOMotorClient = Depends(get_database)):
    collections = await db["collections"].find({"username": username}).to_list(None)
    return collections

@router.get("/{collection_id}/recipes", response_description="List all recipes in a collection")
async def list_recipes_in_collection(collection_id: str, db: AsyncIOMotorClient = Depends(get_database)):
    collection = await db["collections"].find_one({"_id": collection_id})
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    recipes = await db["recipes"].find({"_id": {"$in": collection["recipe_ids"]}}).to_list(None)
    return recipes
