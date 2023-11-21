from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from typing import Optional

class CollectionModel(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    name: str = Field(...)
    description: Optional[str] = Field(None)
    user_id: Optional[str] = Field(None)  # ID of the user who owns the collection
    username: Optional[str] = Field(None)  # Username of the user who owns the collection
    recipe_ids: List[str] = Field(default_factory=list)  # List of recipe IDs
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    favorite: Optional[bool] = Field(None, description="Whether the collection is a favorite collection or not")


class UpdateCollectionModel(BaseModel):
    name: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    recipe_ids: Optional[list] = Field(None)
