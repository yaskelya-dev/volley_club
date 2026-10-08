from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from src.schemas.player import PlayerRead


class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)


class TeamUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=150)


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_by: int
    created_at: datetime


class TeamDetail(TeamRead):
    players: list[PlayerRead] = Field(default_factory=list)
