from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.absence_reason import (
    AbsenceReasonRead,
)
from src.schemas.player import PlayerRead


AttendanceStatus = Literal[
    "present",
    "absent",
    "none",
]


class TrainingCreate(BaseModel):
    date: date
    team_id: int = Field(gt=0)


class TrainingUpdate(BaseModel):
    date: date


class TrainingRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    date: date
    team_id: int
    created_at: datetime


# Существующая схема сохраняется.
class AttendanceUpdate(BaseModel):
    player_id: int = Field(gt=0)
    present: bool


# Существующая схема ответа сохраняется.
class AttendanceRead(BaseModel):
    player_id: int
    present: bool


class AttendanceUpsert(BaseModel):
    player_id: int = Field(gt=0)

    training_id: int = Field(gt=0)

    status: AttendanceStatus

    reason_id: int | None = Field(
        default=None,
        gt=0,
    )


class AttendanceItemRead(BaseModel):
    player_id: int
    training_id: int
    status: AttendanceStatus
    reason_id: int | None
    reason_name: str | None
    is_valid: bool


class AttendanceMarkDTO(BaseModel):
    status: Literal[
        "present",
        "absent",
    ]

    reason_id: int | None = None
    reason_name: str | None = None
    is_valid: bool = False


class AttendanceViewTrainingDTO(BaseModel):
    id: int
    date: date


class AttendanceViewRowDTO(BaseModel):
    row_number: int
    player: PlayerRead
    marks: list[
        AttendanceMarkDTO | None
    ]


class AttendanceViewDTO(BaseModel):
    team_id: int

    trainings: list[
        AttendanceViewTrainingDTO
    ]

    rows: list[
        AttendanceViewRowDTO
    ]

    reasons: list[
        AbsenceReasonRead
    ]


# Старый DTO API /matrix оставлен.
class TrainingMatrixRow(BaseModel):
    row_number: int
    player: PlayerRead
    previous: bool | None
    next_1: bool | None
    next_2: bool | None


class TrainingMatrixResponse(BaseModel):
    selected_training: TrainingRead | None
    trainings: list[TrainingRead]
    rows: list[TrainingMatrixRow]
    selected_attendance: list[AttendanceRead]
