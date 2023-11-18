import random
from .common import *
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid
from typing import List

class UserModel(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    username: str = Field(...)
    email: str = Field(...)
    password: str = Field(...)
    profile_picture: Optional[str] = Field(None)
    bio: Optional[str] = Field(None)
    followers: List[str] = Field(default_factory=list)
    following: List[str] = Field(default_factory=list)
    joining_date: datetime = Field(default_factory=datetime.utcnow)
    is_private: bool = Field(default=False)

    class Config:
        populate_by_name = True
        json_schema_extra = {
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
    is_private: Optional[bool] = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "new_username123",
                "email": "new_email@example.com",
                "password": "password",
                "profile_picture": "new_imgurl",
                "bio": "Updated bio"
            }
        }


class PasswordRecoveryModel(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    email: str = Field(...)
    verification_code: int = Field(
        default_factory=lambda: random.randint(100000, 999999))

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }
