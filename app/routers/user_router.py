from .common import *
from app.models.user_model import UserModel, UpdateUserModel, PasswordRecoveryModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.utils.token import create_access_token
from bson import ObjectId

import random
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

    # Send welcome email after successful user creation
    send_welcome_email(user_email)
    
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


@router.get("/", response_description="List all users")
async def list_users(db: AsyncIOMotorClient = Depends(get_database)):
    users = []
    for doc in await db["users"].find().to_list(length=100):
        if isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        users.append(doc)
    return users


@router.get("/me", response_description="Get current user")
async def get_me(current_user: str = Depends(get_current_user), db: AsyncIOMotorClient = Depends(get_database)):
    user = await db["users"].find_one({"username": current_user["username"]})
    if user:
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
        return user
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/{id}", response_description="Get a single user given its id")
async def show_user(id: str, db: AsyncIOMotorClient = Depends(get_database)):
    if (user := await db["users"].find_one({"_id": id})) is not None:
        # Convert ObjectId back to string for the response
        user["_id"] = str(user["_id"])
        return user

    raise HTTPException(status_code=404, detail=f"User {id} not found")


@router.put("/{id}", response_description="Update a user")
async def update_user(id: str, db: AsyncIOMotorClient = Depends(get_database), user: UpdateUserModel = Body(...), current_user: str = Depends(get_current_user)):
    # Rehash the password if it's being updated
    if user.password:
        user.password = hash_password(user.password)
    user = {k: v for k, v in user.model_dump().items() if v is not None}

    # Compare the current_user id with the value of the id of the user we want to update
    if current_user["user_id"] != id:
        raise HTTPException(
            status_code=403, detail="Forbidden. You don't have permission to update this user.")

    if len(user) >= 1:
        update_result = await db["users"].update_one(
            {"_id": id}, {"$set": user}
        )

        if update_result.modified_count == 1:
            if (
                updated_user := await db["users"].find_one({"_id": id})
            ) is not None:
                # Convert _id to string
                updated_user["_id"] = str(updated_user["_id"])
                return updated_user

    if (
        existing_user := await db["users"].find_one({"_id": id})
    ) is not None:
        # Convert _id to string
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
        print("Email sent")

def send_welcome_email(email: str):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = os.environ.get('EMAIL_USER')  # Fetching from environment variable
    receiver_email = email
    password = os.environ.get('EMAIL_PASS')      # Fetching from environment variable
    message = f"""\
    From: Kasulà <{sender_email}>
    To: {receiver_email}
    Subject: Welcome to Kasulà!

    Thank you for registering with us! We are excited to have you on board."""

    message = message.encode("utf-8")
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
