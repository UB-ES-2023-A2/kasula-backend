from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.routers import user_router, recipe_router, review_router, collection_router


app = FastAPI()

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

# It's deprecated maybe we should change it sometime
@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(settings.DB_URL)
    app.mongodb = app.mongodb_client[settings.DB_NAME]

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

app.include_router(user_router.router, tags=["users"], prefix="/user")
app.include_router(recipe_router.router, tags=["recipes"], prefix="/recipe")
app.include_router(review_router.router, tags=["reviews"], prefix="/review")
app.include_router(collection_router.router, tags=["collections"], prefix="/collection")

@app.get("/")
async def root():
    return {"message": "Hello World!"}
