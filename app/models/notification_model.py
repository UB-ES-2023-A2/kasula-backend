from app.models.common import *
from datetime import datetime
from typing import Optional, Any

class NotificationModel(BaseModel):
    type: str = Field(...)
    text: str = Field(...)
    date: datetime = Field(default_factory=datetime.utcnow)
    image: Optional[str] = Field(None)
    link: str = Field(...)

    # Exemple perquè es vegi en la documentació automàticament generada
    class Config:
        populate_by_name = True # Whether an aliased field may be populated by its name as given by
                                # the model attribute, as well as the alias. Defaults to False.
        json_schema_extra = {
            "example": {
                "type": "follow",
                "text": "User1 has started following you",
                "image": "https://kasula.mooo.com/images/notifications/follow.png",
                "link": "/UserProfile/ivan"
            }
        }
    

# Pq cullons serveix això??
# Per indicar-li quines coses es poden actualitzar?
# class UpdateNotificationModel(BaseModel):
#     pass
