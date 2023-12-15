from typing import List, Optional
from .common import *

from app.models.review_model import ReviewModel, UpdateReviewModel
from app.models.user_model import UserModel
from fastapi import Form, UploadFile, Query
from datetime import datetime
from pathlib import Path
from google.cloud import storage
import json
import time
import os

project_name = 'kasula'
bucket_name = 'bucket-kasula_images'

router = APIRouter()

def get_database(request: Request):
    return request.app.mongodb

@router.post("/{recipe_id}", response_description="Add a review to a recipe")
async def add_review(recipe_id: str, review: str = Form(...), file: Optional[UploadFile] = None, db: AsyncIOMotorClient = Depends(get_database), current_user: UserModel = Depends(get_current_user)):
    # Find the recipe by ID
    recipe = await db["recipes"].find_one({"_id": recipe_id})
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")

    user = await db["users"].find_one({"_id": current_user["user_id"]})

    # Check if the current user is the creator of the recipe
    if recipe.get("username") == user["username"]:
        raise HTTPException(status_code=403, detail="Creators cannot review their own recipes")

    # Check if the recipe is public or if the current user follows the recipe owner
    if not recipe.get("is_public", True):
        recipe_owner = await db["users"].find_one({"username": recipe["username"]})

        if user["username"] not in recipe_owner.get("followers", []):
            raise HTTPException(status_code=403, detail="Cannot review a private recipe without following the creator of the recipe")

    # Check if the current user has already reviewed this recipe
    if any(review["username"] == user["username"] for review in recipe.get("reviews", [])):
        raise HTTPException(status_code=400, detail="User has already reviewed this recipe")

    # Deserialize and handle the review
    review_dict = json.loads(review)
    review_model = ReviewModel(**review_dict)

    if file:
        # Handle file upload and set image URL
        fullname = await upload_image(file, file.filename)
        review_model.image = f'https://storage.googleapis.com/bucket-kasula_images/{fullname}'
    else:
        review_model.image = None

    review_model.username = user["username"]

    # Set user_id to the current user's ID
    review_model.user_id = current_user["user_id"]

    review_dict = jsonable_encoder(review_model)

    # Add the review to the recipe
    update_result = await db["recipes"].update_one(
        {"_id": recipe_id}, {"$push": {"reviews": review_dict}}
    )

    # Recalculate average rating and update it
    updated_recipe = await db["recipes"].find_one({"_id": recipe_id})
    new_average_rating = calculate_average_rating(updated_recipe["reviews"])
    await db["recipes"].update_one(
        {"_id": recipe_id}, {"$set": {"average_rating": new_average_rating}}
    )

    if update_result.modified_count == 1:
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=review_dict)

    raise HTTPException(status_code=500, detail="Failed to add review")


@router.put("/{recipe_id}/{review_id}", response_description="Update a review")
async def update_review(recipe_id: str, review_id: str, update_data: UpdateReviewModel, db: AsyncIOMotorClient = Depends(get_database), current_user: UserModel = Depends(get_current_user)):
    # Retrieve the recipe and check if it exists
    recipe = await db["recipes"].find_one({"_id": recipe_id})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Check if the review exists and if the current user is authorized to update it
    review = next((r for r in recipe["reviews"] if r["_id"] == review_id), None)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    user = await db["users"].find_one({"_id": current_user["user_id"]})

    if review["username"] != user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this review")
    
    # Prepare update data
    if update_data.rating is not None:
        update_data.rating = round(update_data.rating, 1)  # Round to one decimal place
    update_data.updated_date = datetime.utcnow()

    # Create a dictionary for fields to update
    update_fields = {f"reviews.$.{k}": v for k, v in jsonable_encoder(update_data).items() if v is not None}
    
    # Update the review in the database
    update_result = await db["recipes"].update_one(
        {"_id": recipe_id, "reviews._id": review_id},
        {"$set": update_fields}
    )

    # Fetch updated recipe to recalculate average rating
    updated_recipe = await db["recipes"].find_one({"_id": recipe_id})
    new_average_rating = calculate_average_rating(updated_recipe["reviews"])

    # Update the average rating in the database
    await db["recipes"].update_one(
        {"_id": recipe_id}, {"$set": {"average_rating": new_average_rating}}
    )

    if update_result.modified_count == 1:
        modified_fields = {}
        for field in update_fields:
            modified_fields[field.split('.')[-1]] = update_fields[field]
        return modified_fields
        
    raise HTTPException(status_code=404, detail="Recipe or review not found")


@router.delete("/{recipe_id}/{review_id}", response_description="Delete a review")
async def delete_review(recipe_id: str, review_id: str, db: AsyncIOMotorClient = Depends(get_database), current_user: UserModel = Depends(get_current_user)):
    # Retrieve the recipe and check if it exists
    recipe = await db["recipes"].find_one({"_id": recipe_id})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check if the review exists and if the current user is authorized to delete it
    review = next((r for r in recipe["reviews"] if r["_id"] == review_id), None)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    user = await db["users"].find_one({"_id": current_user["user_id"]})

    if review["username"] != user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")
    
    update_result = await db["recipes"].update_one(
        {"_id": recipe_id},
        {"$pull": {"reviews": {"_id": review_id}}}
    )

    # Fetch updated recipe to recalculate average rating
    updated_recipe = await db["recipes"].find_one({"_id": recipe_id})
    new_average_rating = calculate_average_rating(updated_recipe["reviews"])

    # Update the average rating in the database
    await db["recipes"].update_one(
        {"_id": recipe_id}, {"$set": {"average_rating": new_average_rating}}
    )

    if update_result.modified_count == 1:
        return {"message": "Review deleted successfully"}
    raise HTTPException(status_code=404, detail="Recipe or review not found")


@router.get("/{recipe_id}", response_description="List all reviews for a recipe")
async def get_reviews(recipe_id: str, db: AsyncIOMotorClient = Depends(get_database)):
    recipe = await db["recipes"].find_one({"_id": recipe_id})
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")

    return recipe.get("reviews", [])

@router.get("/magic/{recipe_id}", response_description="Get sorted reviews for a recipe")
async def get_sorted_reviews(
    recipe_id: str, 
    sort_by: Optional[str] = Query(None, regex="^(rating|likes|creation_date)$"),
    db: AsyncIOMotorClient = Depends(get_database)
):
    # Find the recipe by ID
    recipe = await db["recipes"].find_one({"_id": recipe_id})
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")

    reviews = recipe.get("reviews", [])

    # Sort the reviews based on the specified criteria
    if sort_by:
        reverse = True if sort_by in ["rating", "likes", "creation_date"] else False  # Assuming higher values are better for rating and likes
        reviews.sort(key=lambda review: review.get(sort_by), reverse=reverse)

    return reviews


@router.patch("/like/{recipe_id}/{review_id}", response_description="Like a review")
async def like_review(recipe_id: str, review_id: str, current_user: UserModel = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    recipe = await db["recipes"].find_one({"_id": recipe_id})

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe or review not found")

    user = await db["users"].find_one({"_id": current_user["user_id"]})

    # Check if the current user has already liked the review or is trying to like their own review
    for review in recipe["reviews"]:
        if review["_id"] == review_id:
            # Check if the current user is trying to like their own review
            if review["username"] == user["username"]:
                raise HTTPException(status_code=403, detail="You cannot like your own review")

            # Check if the current user has already liked the review
            if user["username"] in review.get("liked_by", []):
                raise HTTPException(status_code=400, detail="You have already liked this review")

            # Update the review to add the username to liked_by and increment likes
            update_result = await db["recipes"].update_one(
                {"_id": recipe_id, "reviews._id": review_id},
                {"$inc": {"reviews.$.likes": 1}, "$push": {"reviews.$.liked_by": user["username"]}}
            )

            if update_result.modified_count == 1:
                return {"message": "Review liked successfully"}
            raise HTTPException(status_code=500, detail="An error occurred while liking the review")

    raise HTTPException(status_code=404, detail="Review not found")


@router.patch("/unlike/{recipe_id}/{review_id}", response_description="Unlike a review")
async def unlike_review(recipe_id: str, review_id: str, current_user: UserModel = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    recipe = await db["recipes"].find_one({"_id": recipe_id})

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe or review not found")

    user = await db["users"].find_one({"_id": current_user["user_id"]})

    # Check if the current user has already liked the review
    for review in recipe["reviews"]:
        if review["_id"] == review_id:
            # Check if the current user has liked the review
            if user["username"] not in review.get("liked_by", []):
                raise HTTPException(status_code=400, detail="You have not liked this review")

            # Update the review to remove the username from liked_by and decrement likes
            update_result = await db["recipes"].update_one(
                {"_id": recipe_id, "reviews._id": review_id},
                {"$inc": {"reviews.$.likes": -1}, "$pull": {"reviews.$.liked_by": user["username"]}}
            )

            if update_result.modified_count == 1:
                return {"message": "Review unliked successfully"}
            raise HTTPException(status_code=500, detail="An error occurred while unliking the review")

    raise HTTPException(status_code=404, detail="Review not found")

def calculate_average_rating(reviews: List[dict]) -> float:
    if not reviews:
        return 0.0
    total_rating = sum(review['rating'] for review in reviews if 'rating' in review)
    return total_rating / len(reviews)

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