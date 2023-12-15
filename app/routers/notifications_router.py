from app.routers.common import *
from app.models.notification_model import NotificationModel
from typing import List

router = APIRouter(tags=["notifications"], prefix="/notification")

def get_database(request: Request):
    return request.app.mongodb

@router.post("/{username}", response_description="Add a notification to a user")
async def add_notification(username: str, notification: NotificationModel, db: AsyncIOMotorClient = Depends(get_database)):
    user = await db["users"].find_one({"username": username}) # Si canviés coses directament a usuari,
    # aquests canvis no es veurien reflectits en la base de dades, perquè tant sols està en la memòria
    # i no s'apliquen les modificacions a la base de dades si no li diem explícitament que ho faci
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await db["users"].update_one({"username": username},
                                 {"$push": {"notifications": notification.model_dump()}})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=jsonable_encoder(notification))

# Method to change the status of a notification from unread to read
@router.put("/{username}/{notification_id}", response_description="Change the status of a notification")
async def change_notification_status(username: str, notification_id: str, mystatus: str,
                                     db: AsyncIOMotorClient = Depends(get_database)):
    user = await db["users"].find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    for notification in user['notifications']:
        if notification['id'] == notification_id:
            notification['status'] = mystatus
            await db["users"].update_one({"username": username},
                                         {"$set": {"notifications": user['notifications']}})
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(notification))
    raise HTTPException(status_code=404, detail="Notification not found")

@router.get("/{username}", response_description="Get all notifications from a user")
async def get_notifications(username: str, db: AsyncIOMotorClient = Depends(get_database)) -> List[NotificationModel]:
    user = await db["users"].find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(user['notifications']) if 'notifications' in user else [])