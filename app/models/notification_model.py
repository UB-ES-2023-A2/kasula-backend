from app.models.common import *
from datetime import datetime
from typing import Optional, Any

class NotificationModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id") # String pq es pugui serialitzar
    date: datetime = Field(default_factory=datetime.utcnow)
    type: str = Field(...)
    username: str = Field(...)
    text: str = Field(...)
    status: str = Field(default="unread") # unread, read, deleted
    image: Optional[str] = Field(None)
    link: str = Field(...)

    # Exemple perquè es vegi en la documentació automàticament generada
    class Config:
        populate_by_name = True # Whether an aliased field may be populated by its name as given by
                                # the model attribute, as well as the alias. Defaults to False.
        json_schema_extra = {
            "example": {
                "type": "follow",
                "text": "t'ha deixat de seguir",
                "username": "andreu",
                "image": "https://as2.ftcdn.net/v2/jpg/01/98/33/63/1000_F_198336329_D3JsfuSGm5UBTXR9fwcr2WhKNebr7SiB.jpg",
                "link": "/UserProfile/ivan"
            }
        }

# Pq cullons serveix això??
# Per indicar-li quines coses es poden actualitzar?
# class UpdateNotificationModel(BaseModel):
#     pass
