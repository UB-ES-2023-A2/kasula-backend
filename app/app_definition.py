import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.routers import user_router, recipe_router, review_router, collection_router

# Define the startup and shutdown logic using async context manager
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Startup logic
    if settings.TEST_ENV:
        app.mongodb_client = AsyncIOMotorClient(settings.DB_URL)
        app.mongodb = app.mongodb_client[settings.DB_TEST]

        # Clear the collections before running the tests
        await app.mongodb["users"].drop()
        await app.mongodb["recipes"].drop()
        await app.mongodb["collections"].drop()

    else:
        app.mongodb_client = AsyncIOMotorClient(settings.DB_URL)
        app.mongodb = app.mongodb_client[settings.DB_NAME]
    
    yield  # The application runs while this yield is active

    # Shutdown logic
    app.mongodb_client.close()

app = FastAPI(lifespan=app_lifespan)

# Allow all origins for development purposes, to be able to use
# the local / deployed backend either with a local or deployed frontend.
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router.router, tags=["users"], prefix="/user")
app.include_router(recipe_router.router, tags=["recipes"], prefix="/recipe")
app.include_router(review_router.router, tags=["reviews"], prefix="/review")
app.include_router(collection_router.router, tags=["collections"], prefix="/collection")

@app.get("/")
async def root():
    return {"message": "Hello World!"}
