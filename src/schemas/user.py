from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6, max_length=72)


class UserLogin(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=1, max_length=72)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class MessageResponse(BaseModel):
    message: str
