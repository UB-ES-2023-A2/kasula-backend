from .common import *
from app.models.user_model import UserModel, UpdateUserModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.utils.token import create_access_token
from bson import ObjectId

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

def get_database(request: Request):
    return request.app.mongodb

@router.post("/", response_description="Add new user")
async def create_user(request: Request, user: UserModel = Body(...), db: AsyncIOMotorClient = Depends(get_database)):
    
    # Check if username or email already exists in the database
    existing_user = await db["users"].find_one({"$or": [{"username": user.username}, {"email": user.email}]})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")

    # Hash the password before storing
    hashed_password = hash_password(user.password)
    user = jsonable_encoder(user)
    user["hashed_password"] = hashed_password
    del user["password"]  # Remove plain password from the dict
    
    new_user = await db["users"].insert_one(user)
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})

    if isinstance(created_user["_id"], ObjectId):
        created_user["_id"] = str(created_user["_id"])
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
    try:
        # Convert the string id to ObjectId type
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
    
    if (user := await db["users"].find_one({"_id": oid})) is not None:
        # Convert ObjectId back to string for the response
        user["_id"] = str(user["_id"])
        return user

    raise HTTPException(status_code=404, detail=f"User {id} not found")

@router.put("/{id}", response_description="Update a user")
async def update_user(id: str, db: AsyncIOMotorClient = Depends(get_database), user: UpdateUserModel = Body(...), current_user: str = Depends(get_current_user)):
    user = {k: v for k, v in user.model_dump().items() if v is not None}

    # Compare the current_user id with the value of the id of the user we want to update
    if current_user["user_id"] != id:
        raise HTTPException(status_code=403, detail="Forbidden. You don't have permission to update this user.")

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
        raise HTTPException(status_code=403, detail="Forbidden: You don't have permission to delete this user.")
    
    delete_result = await db["users"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "User successfully deleted"})
    
    raise HTTPException(status_code=404, detail=f"User {id} not found")

@router.get("/check_username/{username}", response_description="Check if username is already taken")
async def check_username(username: str, db: AsyncIOMotorClient = Depends(get_database)):
    user = await db["users"].find_one({"username": username})
    print(user)
    if user:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "Username already taken", "status": False})
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Username available", "status": True})

@router.get("/check_email/{email}", response_description="Check if email exists in the database")
async def check_email(email: str, db: AsyncIOMotorClient = Depends(get_database)):
    user = await db["users"].find_one({"email": email})
    if user:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "Email already registered", "status": False})
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Email available", "status": True})

@router.post("/token", response_description="Token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncIOMotorClient = Depends(get_database)):
    user = await db["users"].find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = str(user["_id"])  # Convert the user ID (if it's an ObjectId from MongoDB) to string
    username = user["username"]
    access_token = create_access_token(data={"sub": username}, user_id=user_id, username=username)
    return {"access_token": access_token, "token_type": "bearer"}