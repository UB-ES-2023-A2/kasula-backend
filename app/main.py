import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

from routers import user_router

app = FastAPI()

print("ENVIRONMENT VARIABLES")
print("DEBUG_MODE: " + str(settings.DEBUG_MODE))
print("DB_URL: " + settings.DB_URL)
print("DB_NAME: " + settings.DB_NAME)

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(settings.DB_URL)
    app.mongodb = app.mongodb_client[settings.DB_NAME]


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()


app.include_router(user_router.router, tags=["users"], prefix="/user")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        reload=settings.DEBUG_MODE,
        port=settings.PORT,
    )