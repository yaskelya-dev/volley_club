from pydantic import BaseModel, ConfigDict, Field


class AbsenceReasonCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=200,
    )

    is_valid: bool = False


class AbsenceReasonUpdate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=200,
    )

    is_valid: bool = False


class AbsenceReasonRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    created_by: int
    is_valid: bool
