from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from bson import ObjectId


class CVRequest(BaseModel):
    link: str


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: Any, handler: Any) -> Any:
        """Return a JSON schema that represents ObjectId as string"""
        return {"type": "string"}


class Profile(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    linkedin_username: str
    full_name: str
    email: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    about: Optional[str] = None
    experience: List[dict] = []
    education: List[dict] = []
    skills: List[str] = []
    languages: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True
