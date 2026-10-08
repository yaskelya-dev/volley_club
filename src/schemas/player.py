from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PlayerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)


class PlayerUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=150)


class PlayerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_by: int
    created_at: datetime
