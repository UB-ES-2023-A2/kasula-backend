import uuid
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class ReviewModel(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    username: Optional[str] = Field(None)
    rating: float = Field(..., ge=1, le=5)  # Rating between 1 and 5
    comment: Optional[str] = Field(None)
    image: Optional[str] = Field(None)  # URL of the image
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    updated_date: datetime = Field(default_factory=datetime.utcnow)
    likes: int = Field(default=0)
    liked_by: List[str] = Field(default_factory=list)
    user_id: str = Field(None)

    @validator('rating')
    def validate_rating(cls, v):
        if round(v, 1) != v:
            raise ValueError('Rating must have only one decimal place')
        return v

class UpdateReviewModel(BaseModel):
    rating: Optional[float] = Field(None, ge=1, le=5)  # Rating between 1 and 5, with one decimal place
    comment: Optional[str] = Field(None)
    image: Optional[str] = Field(None)
    updated_date: Optional[datetime] = None
    likes: Optional[int] = None
    user_id: Optional[str] = Field(None)
