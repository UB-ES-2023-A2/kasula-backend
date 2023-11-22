from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from mongomock_motor import AsyncMongoMockClient

from app.config import settings
from app.routers import user_router, recipe_router, review_router, collection_router

# Define the startup and shutdown logic using async context manager
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    settings.TEST_ENV = True
    # Startup logic
    app.mongodb_client = AsyncMongoMockClient()
    app.mongodb = app.mongodb_client[settings.DB_TEST]
    
    yield  # The application runs while this yield is active

    # Shutdown logic
    settings.TEST_ENV = False
    app.mongodb_client.close()

# Initialize FastAPI with the new lifespan parameter
unit_tests = FastAPI(lifespan=app_lifespan)

# CORS and other configurations
origins = ["*"]
unit_tests.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your routers
unit_tests.include_router(user_router.router, tags=["users"], prefix="/user")
unit_tests.include_router(recipe_router.router, tags=["recipes"], prefix="/recipe")
unit_tests.include_router(review_router.router, tags=["reviews"], prefix="/review")
unit_tests.include_router(collection_router.router, tags=["collections"], prefix="/collection")

@unit_tests.get("/")
async def root():
    return {"message": "Hello World!"}
