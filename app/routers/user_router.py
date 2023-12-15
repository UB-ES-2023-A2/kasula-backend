from .common import *
from app.models.user_model import UserModel, UpdateUserModel, PasswordRecoveryModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.utils.token import create_access_token
from bson import ObjectId
from email.mime.text import MIMEText
from fastapi import Form, UploadFile, File, HTTPException, Depends
from google.cloud import storage
import time
from pathlib import Path
from typing import List, Optional
import json
import uuid
from app.config import settings

project_name = 'kasula'
bucket_name = 'bucket-kasula_images'

import smtplib
import ssl
import os

# Suppress UserWarning from pydantic
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

def get_database(request: Request):
    return request.app.mongodb


def is_valid_email(email: str) -> bool:
    """Check if provided email has a valid format."""
    regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(regex, email) is not None


@router.post("/", response_description="Add new user")
async def create_user(request: Request, user: UserModel = Body(...), db: AsyncIOMotorClient = Depends(get_database)):
    user_email = user.email
    # Check if email has a valid format
    if not is_valid_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")

    # Check if username or email already exists in the database
    existing_user = await db["users"].find_one({"$or": [{"username": user.username}, {"email": user.email}]})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username or email already registered")

    # Hash the password before storing
    password = hash_password(user.password)
    user = jsonable_encoder(user)
    user["password"] = password

    new_user = await db["users"].insert_one(user)
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})

    if isinstance(created_user["_id"], ObjectId):
        created_user["_id"] = str(created_user["_id"])

    collection = {
        "_id": str(uuid.uuid4()),  # Explicitly set the _id field with a UUID
        "name": "Favorites",
        "description": "Here you can see your favorite recipes!",
        "recipe_ids": [],
        "user_id": created_user["_id"],
        "username": created_user["username"],
        "favorite": True
    }

    await db["collections"].insert_one(jsonable_encoder(collection))

    # Send welcome email after successful user creation
    if not settings.TEST_ENV:
        send_welcome_email(user_email)
    
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


@router.get("/", response_description="List all users")
async def list_users(db: AsyncIOMotorClient = Depends(get_database)):
    users = []
    for doc in await db["users"].find().to_list(length=100):
        if isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        doc.pop("password", None)  # Remove the password field
        users.append(doc)
    return users


@router.get("/me", response_description="Get current user")
async def get_me(current_user: str = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    user = await db["users"].find_one({"_id": current_user["user_id"]})
    if user:
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
        user.pop("password", None)  # Remove the password field
        return user
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/{identifier}", response_description="Get a single user given its id or username")
async def show_user(identifier: str, db: AsyncIOMotorClient = Depends(get_database)):
    query = {"$or": [{"_id": identifier}, {"username": identifier}]}
    if (user := await db["users"].find_one(query)) is not None:
        # Convert ObjectId back to string for the response
        user["_id"] = str(user["_id"])
        user.pop("password", None)  # Remove the password field
        return user

    raise HTTPException(status_code=404, detail=f"User {identifier} not found")

@router.put("/{id}", response_description="Update a user")
async def update_user(
    id: str, 
    db: AsyncIOMotorClient = Depends(get_database), 
    user: Optional[str] = Form(None),  # Make the user data optional
    file: UploadFile | None = None,  # File upload
    current_user: str = Depends(get_current_user)
):
    user_update = {}

    # Retrieve the current user from the database
    actual_user = await db["users"].find_one({"_id": current_user["user_id"]})

    # Only parse user data if it's provided
    if user:
        user_data = json.loads(user)
        user_model = UpdateUserModel(**user_data)

        if user_model.password:
            user_model.password = hash_password(user_model.password)

        user_update = {k: v for k, v in user_model.dict().items() if v is not None}

    if current_user["user_id"] != id:
        raise HTTPException(
            status_code=403, detail="Forbidden. You don't have permission to update this user.")

    # Image processing and uploading
    if file:
        fullname = await upload_image(file, file.filename)
        image_url = f'https://storage.googleapis.com/bucket-kasula_images/{fullname}'

        user_update['profile_picture'] = image_url

    # Ensure there's something to update
    if user_update:
        update_result = await db["users"].update_one(
            {"_id": id}, {"$set": user_update}
        )

        if 'username' in user_update and not settings.TEST_ENV:
            # Update the username in all recipes created by the user
            await db["recipes"].update_many(
                {"user_id": id}, {"$set": {"username": user_update["username"]}}
            )
            # Update the username in all reviews within the recipes
            await db["recipes"].update_many(
                {"reviews.user_id": id},
                {"$set": {"reviews.$[elem].username": user_update["username"]}},
                array_filters=[{"elem.user_id": id}]
            )
            await db["collections"].update_many(
                {"user_id": id}, {"$set": {"username": user_update["username"]}}
            )
            # Update the username in all followers of the current user
            await db["users"].update_many(
                {"following": actual_user["username"]},
                {"$set": {"following.$": user_update["username"]}}
            )
            # Update the username in all following of the current user
            await db["users"].update_many(
                {"followers": actual_user["username"]},
                {"$set": {"followers.$": user_update["username"]}}
            )

        if update_result.modified_count == 1:
            if (
                updated_user := await db["users"].find_one({"_id": id})
            ) is not None:
                updated_user["_id"] = str(updated_user["_id"])
                return updated_user

    if (
        existing_user := await db["users"].find_one({"_id": id})
    ) is not None:
        existing_user["_id"] = str(existing_user["_id"])
        return existing_user

    raise HTTPException(status_code=404, detail=f"User {id} not found")


@router.delete("/{id}", response_description="Delete User")
async def delete_user(id: str, db: AsyncIOMotorClient = Depends(get_database), current_user: str = Depends(get_current_user)):
    # Fetch the user you want to delete from the database
    user_to_delete = await db["users"].find_one({"_id": id})

    # If user is not found, raise 404 exception
    if user_to_delete is None:
        raise HTTPException(status_code=404, detail=f"User {id} not found")

    # Compare the current_user with the username of the fetched user
    if current_user["username"] != user_to_delete["username"]:
        raise HTTPException(
            status_code=403, detail="Forbidden: You don't have permission to delete this user.")

    delete_result = await db["users"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "User successfully deleted"})

    raise HTTPException(status_code=404, detail=f"User {id} not found")


@router.get("/check_username/{username}", response_description="Check if username is already taken")
async def check_username(username: str, db: AsyncIOMotorClient = Depends(get_database)):
    user = await db["users"].find_one({"username": username})
    if user:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Username already taken", "status": False})
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Username available", "status": True})


@router.get("/check_email/{email}", response_description="Check if email exists in the database")
async def check_email(email: str, db: AsyncIOMotorClient = Depends(get_database)):
    user = await db["users"].find_one({"email": email})
    if user:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Email already registered", "status": False})
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Email available", "status": True})


@router.post("/token", response_description="Token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncIOMotorClient = Depends(get_database)):
    if '@' in form_data.username:
        user = await db["users"].find_one({"email": form_data.username})
    else:
        user = await db["users"].find_one({"username": form_data.username})

    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Convert the user ID (if it's an ObjectId from MongoDB) to string
    user_id = str(user["_id"])
    username = user["username"]
    access_token = create_access_token(
        data={"sub": username}, user_id=user_id, username=username)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/password_recovery", response_description="Password recovery")
async def password_recovery(request: Request, document: PasswordRecoveryModel, db: AsyncIOMotorClient = Depends(get_database)):
    # Remove any existing password recovery documents for this email
    deleted_documents = await db["password_recovery"].delete_many({"email": document.email})
    if not deleted_documents:
        raise HTTPException(
            status_code=500, detail="Something went wrong")
    document = jsonable_encoder(document)
    nonhashed_verification_code = document["verification_code"]
    document["verification_code"] = hash_password(
        str(document["verification_code"]))
    # Create a new password recovery document
    created_document = await db["password_recovery"].insert_one(document)
    if created_document:
        # Send email with verification code
        send_email(document["email"], nonhashed_verification_code)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "Password recovery document created"})
    raise HTTPException(status_code=500, detail="Something went wrong")


@router.put("/password_recovery/{email}", response_description="Update password")
async def update_password(email: str, verification_code: int, user: UpdateUserModel = Body(...), db: AsyncIOMotorClient = Depends(get_database)):
    document = await db["password_recovery"].find_one({"email": email})
    if document:
        if verify_password(str(verification_code), document["verification_code"]):
            # Delete the password recovery document
            deleted_document = await db["password_recovery"].delete_one({"email": email})
            if not deleted_document:
                raise HTTPException(
                    status_code=500, detail="Something went wrong")
            # Rehash the password if it's being updated
            if user.password:
                user.password = hash_password(user.password)
            user = {k: v for k, v in user.model_dump().items()
                    if v is not None}

            if len(user) >= 1:
                update_result = await db["users"].update_one(
                    {"email": email}, {"$set": user}
                )

                if update_result.modified_count == 1:
                    if (
                        updated_user := await db["users"].find_one({"email": email})
                    ) is not None:
                        # Convert _id to string
                        updated_user["_id"] = str(updated_user["_id"])
                        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Verification successful", "status": True, "user": updated_user})

            if (
                existing_user := await db["users"].find_one({"email": email})
            ) is not None:
                # Convert _id to string
                existing_user["_id"] = str(existing_user["_id"])
                return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Verification successful", "status": True, "user": existing_user})
        else:
            return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Verification failed", "status": False})

    raise HTTPException(status_code=404, detail=f"Email {email} not found")

@router.post("/follow/{username}", response_description="Follow a user by username")
async def follow_user(username: str, current_user: str = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    # Retrieve the current user from the database
    actual_user = await db["users"].find_one({"_id": current_user["user_id"]})

    # Find the target user by username
    target_user = await db["users"].find_one({"username": username})

    if not target_user:
        raise HTTPException(status_code=404, detail=f"User {username} not found")

    target_username = target_user["username"]

    # Prevent self-follow
    if target_username == actual_user["username"]:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    # Check if the target user is already in the current user's following list
    if target_username in actual_user["following"]:
        raise HTTPException(status_code=400, detail=f"You are already following user {username}")

    # Update the current user's following list
    await db["users"].update_one(
        {"username": actual_user["username"]},
        {"$addToSet": {"following": target_username}}
    )

    # Update the target user's followers list
    await db["users"].update_one(
        {"username": target_username},
        {"$addToSet": {"followers": actual_user["username"]}}
    )

    return {"message": f"Now following user {username}"}

@router.post("/unfollow/{username}", response_description="Unfollow a user by username")
async def unfollow_user(username: str, current_user: str = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    # Retrieve the current user from the database
    actual_user = await db["users"].find_one({"_id": current_user["user_id"]})

    # Find the target user by username
    target_user = await db["users"].find_one({"username": username})
    if not target_user:
        raise HTTPException(status_code=404, detail=f"User {username} not found")

    target_username = target_user["username"]

    # Check if the target user is in the current user's following list
    if target_username not in actual_user["following"]:
        raise HTTPException(status_code=400, detail=f"You are not following user {username}")

    # Check if the target user is the same as the current user
    if target_username == actual_user["username"]:
        raise HTTPException(status_code=400, detail="Cannot unfollow yourself")

    # Update the current user's following list
    await db["users"].update_one(
        {"username": actual_user["username"]},
        {"$pull": {"following": target_username}}
    )

    # Update the target user's followers list
    await db["users"].update_one(
        {"username": target_username},
        {"$pull": {"followers": actual_user["username"]}}
    )

    return {"message": f"Unfollowed user {username}"}


def send_email(email: str, verification_code: int):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = os.environ.get('EMAIL_USER')  # Fetching from environment variable
    receiver_email = email
    password = os.environ.get('EMAIL_PASS')      # Fetching from environment variable
    message = f"""\
    From: Kasulà <{sender_email}>
    To: {receiver_email}
    Subject: Password Recovery

    Your verification code is: {verification_code}"""

    message = message.encode("utf-8")
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message)

def send_welcome_email(email: str):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = os.environ.get('EMAIL_USER')  # Fetching from environment variable
    receiver_email = email
    password = os.environ.get('EMAIL_PASS')      # Fetching from environment variable

    # Create the email message
    subject = "Welcome to Kasulà!"
    body = "Thank you for registering with us! We are excited to have you on board."
    message = MIMEText(body, 'plain')
    message['From'] = f"Kasulà <{sender_email}>"
    message['To'] = receiver_email
    message['Subject'] = subject

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.send_message(message)

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

@router.get("/new/discover", response_description="List all users randomly")
async def list_users_randomly(current_user: str = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    # Retrieve the current user from the database
    actual_user = await db["users"].find_one({"_id": current_user["user_id"]})

    if not actual_user["following"]:
        users = []
        for doc in await db["users"].aggregate([{"$match": {"_id": {"$ne": actual_user["_id"]}}}, {"$sample": {"size": 10}}]).to_list(length=10):
            if isinstance(doc["_id"], ObjectId):
                doc["_id"] = str(doc["_id"])
            doc.pop("password", None)  # Remove the password field
            users.append(doc)
        return users
    else:
        raise HTTPException(status_code=400, detail="Cannot list users randomly if following list is not empty")