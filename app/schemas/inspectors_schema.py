from pydantic import BaseModel, Field, model_validator, ValidationError
from typing import Optional, Literal, List, Any
from uuid import UUID
from datetime import datetime, timezone, date
from .enums import ProjectType, WeekdayEnum, InspectionWindowEnum
from fastapi import Form, File, UploadFile, Depends


class SuccessResponse(BaseModel):
    success: bool = True
    status_code: int = 200
    message: str
    data: Optional[Any] = None


class InspectorCreationSetupDTO(BaseModel):
    user_id: str = Field(
        ..., description="the user id of the inspector to invite to the project"
    )
    start_date: date = Field(
        ..., description="The inspection date for the inspector start date (YYYY-MM-DD)"
    )
    end_date: date = Field(
        ..., description="The inspection date for the inspector (YYYY-MM-DD)"
    )

    visit_type: Literal[
        "Routine_site_visit", "Milestone_Verification", "Emergence_Review"
    ] = Field(..., description="The Type of Vist Of the Inspector")

    note: Optional[str] = Field(None, description="The note for the inspector")
    notify_me: bool = Field(default=False)

    @model_validator(mode="before")
    def validate_dates(cls, values: dict) -> dict:
        start = values.get("start_date")
        end = values.get("end_date")

        # Only enforce logical order when BOTH are provided
        if start and end and end < start:
            raise ValueError("end_date must be after start_date")

        return values
