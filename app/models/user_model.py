from .common import *
from typing import Optional
import uuid

class UserModel(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    username: str = Field(...)
    email: str = Field(...)
    password: str = Field(...)
    profile_picture: Optional[str] = Field(None)
    bio: Optional[str] = Field(None)
    
    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "id": "00010203-0405-0607-0809-0a0b0c0d0e0f",
                "username": "username123",
                "email": "username123@example.com",
                "password": "password",
                "profile_picture": "imgurl",
                "bio": "This is a short bio"
            }
        }

class UpdateUserModel(BaseModel):
    username: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    password: Optional[str] = Field(None)
    profile_picture: Optional[str] = Field(None)
    bio: Optional[str] = Field(None)

    class Config:
        schema_extra = {
            "example": {
                "username": "new_username123",
                "email": "new_email@example.com",
                "password": "password",
                "profile_picture": "new_imgurl",
                "bio": "Updated bio"
            }
        }
