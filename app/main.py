import uvicorn
from app.config import settings
from app.app_definition import app

# print("\nENVIRONMENT VARIABLES")
# print("DEBUG_MODE: " + str(settings.DEBUG_MODE))
# print("DB_URL: " + settings.DB_URL)
# print("DB_NAME: " + settings.DB_NAME + "\n")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        reload=settings.DEBUG_MODE,
        port=settings.PORT,
    )
