from .common import *
from app.models.collection_model import CollectionModel, UpdateCollectionModel
from app.models.user_model import UserModel
from typing import Optional, Dict

router = APIRouter()

def get_database(request: Request):
    return request.app.mongodb

@router.post("/", response_description="Create a new collection")
async def create_collection(collection: CollectionModel = Body(...), current_user: UserModel = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    collection.user_id = str(current_user["user_id"])

    # Retrieve the current user from the database
    user = await db["users"].find_one({"_id": current_user["user_id"]})

    collection.username = user["username"]

    # Check if the user already has a collection with the same name
    existing_collection = await db["collections"].find_one({"username": collection.username, "name": collection.name})
    
    if existing_collection:
        raise HTTPException(status_code=400, detail="A collection with the same name already exists for this user")

    new_collection = await db["collections"].insert_one(jsonable_encoder(collection))
    created_collection = await db["collections"].find_one({"_id": new_collection.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_collection)

@router.delete("/{collection_id}", response_description="Delete a collection")
async def delete_collection(collection_id: str, current_user: UserModel = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    collection = await db["collections"].find_one({"_id": collection_id})

    if not collection.get("favorite", False):
        if collection and collection["user_id"] == str(current_user["user_id"]):
            await db["collections"].delete_one({"_id": collection_id})
            return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Collection deleted"})
        else:
            raise HTTPException(status_code=404, detail="Collection not found or access denied")
    else:
        raise HTTPException(status_code=403, detail="Cannot delete a favorite collection")

@router.put("/{collection_id}", response_description="Update a collection")
async def update_collection(collection_id: str, update_data: UpdateCollectionModel = Body(...), current_user: UserModel = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    collection = await db["collections"].find_one({"_id": collection_id})
    if collection and collection["user_id"] == str(current_user["user_id"]):
        if "name" in update_data.dict():
            existing_collection = await db["collections"].find_one({"username": collection["username"], "name": update_data.name})
            if existing_collection:
                raise HTTPException(status_code=400, detail="A collection with the same name already exists for this user")
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
async def list_collections_by_user(username: str, db: AsyncIOMotorClient = Depends(get_database), current_user: Optional[Dict[str, str]] = Depends(get_current_user)):
    # Current user
    actual_user = current_user["username"] if current_user else None
    
    # Retrieve the user from the database
    user = await db["users"].find_one({"username": username})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.get("is_private", False) or actual_user == username or (actual_user and actual_user in user.get("followers", [])):
        collections = await db["collections"].find({"username": username}).to_list(None)
        return collections
    else:
        raise HTTPException(status_code=403, detail="User is not public")
    
@router.get("/{collection_id}/recipes", response_description="List all recipes in a collection")
async def list_recipes_in_collection(collection_id: str, db: AsyncIOMotorClient = Depends(get_database), current_user: Optional[Dict[str, str]] = Depends(get_current_user)):
    # Current user
    actual_user = current_user["username"] if current_user else None

    collection = await db["collections"].find_one({"_id": collection_id})

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Get the user that owns the collection
    user = await db["users"].find_one({"username": collection["username"]})

    # Check if the user creator of the collection is public
    if not user.get("is_private", False):
        recipes = await db["recipes"].find({"_id": {"$in": collection["recipe_ids"]}}).to_list(None)
        return recipes
    else:
        # Check if the current user is following the user
        if actual_user and actual_user in user.get("followers", []):
            recipes = await db["recipes"].find({"_id": {"$in": collection["recipe_ids"]}}).to_list(None)
            return recipes
        else:
            raise HTTPException(status_code=403, detail="Access denied")
        
@router.get("/favorites/{username}", response_description="Get the favorites collection of a user")
async def get_favorites_collection(username: str, db: AsyncIOMotorClient = Depends(get_database), current_user: Optional[Dict[str, str]] = Depends(get_current_user)):
    # Current user
    username = current_user["username"] if current_user else None

    if username:
        user = await db["users"].find_one({"username": username})

        if current_user["user_id"] == user["_id"]:
            if user:
                collection = await db["collections"].find_one({"username": username, "favorite": True})
                if collection:
                    return collection
                else:
                    raise HTTPException(status_code=404, detail="Favorites collection not found")
            else:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            raise HTTPException(status_code=403, detail="Access denied")
        
    else:
        raise HTTPException(status_code=403, detail="Access denied")

@router.patch("/favorites/add_recipe/{recipe_id}", response_description="Add a recipe to the favorites collection of the current user")
async def add_recipe_to_favorites(recipe_id: str, current_user: UserModel = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    collection = await db["collections"].find_one({"username": current_user["username"], "favorite": True})
    if collection:
        await db["collections"].update_one({"_id": collection["_id"]}, {"$addToSet": {"recipe_ids": recipe_id}})
        updated_collection = await db["collections"].find_one({"_id": collection["_id"]})
        return updated_collection
    else:
        raise HTTPException(status_code=404, detail="Favorites collection not found")

@router.patch("/favorites/remove_recipe/{recipe_id}", response_description="Remove a recipe from the favorites collection of the current user")
async def remove_recipe_from_favorites(recipe_id: str, current_user: UserModel = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    collection = await db["collections"].find_one({"username": current_user["username"], "favorite": True})
    if collection:
        await db["collections"].update_one({"_id": collection["_id"]}, {"$pull": {"recipe_ids": recipe_id}})
        updated_collection = await db["collections"].find_one({"_id": collection["_id"]})
        return updated_collection
    else:
        raise HTTPException(status_code=404, detail="Favorites collection not found")
