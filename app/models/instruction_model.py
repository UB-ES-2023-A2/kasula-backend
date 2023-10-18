from .common import *

class InstructionModel(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    body: str = Field(...)
    step_number: int = Field(...)
    #image: Optional[str] = Field(None)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "00010203-0405-0607-0809-0a0b0c0d0e0f",
                "body": "Recipe Name",
                "step_number": 1,
                #"image": "imgurl",
            }
        }

class UpdateInstructionModel(BaseModel):
    body: Optional[str]
    step_number: Optional[int]
    #image: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "body": "Recipe Name",
                "step_number": 1,
                #"image": "imgurl",
            }
        }