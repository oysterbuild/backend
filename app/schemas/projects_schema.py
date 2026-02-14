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


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    project_type: str
    location_text: str
    location_map: Optional[str]
    start_date: date
    end_date: date
    budget: float
    budget_currency: str
    status: str
    payment_status: str
    owner_id: UUID
    plan_id: Optional[UUID]
    preferred_inspection_days: List[str]
    preferred_inspection_window: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # 🔑 REQUIRED


class ProjectSetupDto(BaseModel):
    name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Detailed description of the project")
    project_type: ProjectType = Field(
        ..., description="Type of project (Residential, Commercial, Infrastructure)"
    )
    location_text: str = Field(..., description="Text representation of the location")
    location_map: Optional[str] = Field(None, description="Map coordinates or map URL")
    start_date: date = Field(..., description="Project start date -YYYY-MM-DD")
    end_date: date = Field(..., description="Project end date")
    budget: float = Field(..., description="Total budget for the project")
    budget_currency: Optional[Literal["NGN", "USD"]] = Field(
        "NGN", description="Currency of the budget"
    )
    status: Literal["Active", "Completed", "Pending", "Draft"] = Field(
        ..., description="Current status of the project"
    )
    plan_id: UUID = Field(..., description="ID of the associated plan")

    preferred_inspection_days: Optional[List[WeekdayEnum]] = Field(
        None, description="Days of the week preferred for inspections"
    )
    preferred_inspection_window: Optional[InspectionWindowEnum] = Field(
        None, description="Preferred time window for inspections"
    )

    @model_validator(mode="before")
    def check_dates(cls, values: dict) -> dict:
        now = datetime.now(timezone.utc).date()

        start = values.get("start_date")
        end = values.get("end_date")

        # Remove tzinfo if present
        if start and start < now:
            raise ValueError("start_date must not be in the past")
        if end and end < now:
            raise ValueError("end_date must not be in the past")
        if start and end and end < start:
            raise ValueError("end_date must be after start_date")

        return values


class ProjectSetupUpdateDto(BaseModel):
    name: Optional[str] = Field(None, description="Name of the project")
    description: Optional[str] = Field(
        None, description="Detailed description of the project"
    )
    project_type: Optional[ProjectType] = Field(
        None, description="Type of project (Residential, Commercial, Infrastructure)"
    )
    location_text: Optional[str] = Field(
        None, description="Text representation of the location"
    )
    location_map: Optional[str] = Field(None, description="Map coordinates or map URL")

    start_date: Optional[date] = Field(
        None, description="Project start date (YYYY-MM-DD)"
    )
    end_date: Optional[date] = Field(None, description="Project end date (YYYY-MM-DD)")

    budget: Optional[float] = Field(None, description="Total budget for the project")
    budget_currency: Optional[Literal["NGN", "USD"]] = Field(
        None, description="Currency of the budget"
    )

    status: Optional[Literal["Active", "Pending", "Draft"]] = Field(
        None, description="Current status of the project"
    )

    plan_id: Optional[UUID] = Field(None, description="ID of the associated plan")

    preferred_inspection_days: Optional[List[WeekdayEnum]] = Field(
        None, description="Days of the week preferred for inspections"
    )
    preferred_inspection_window: Optional[InspectionWindowEnum] = Field(
        None, description="Preferred time window for inspections"
    )

    existing_image_ids: Optional[List[UUID]] = []

    @model_validator(mode="before")
    def validate_dates(cls, values: dict) -> dict:
        start = values.get("start_date")
        end = values.get("end_date")

        # Only enforce logical order when BOTH are provided
        if start and end and end < start:
            raise ValueError("end_date must be after start_date")

        return values

class UpdateProjectForm:
    def __init__(
        self,
        name: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        project_type: Optional[ProjectType] = Form(None),
        location_text: Optional[str] = Form(None),
        location_map: Optional[str] = Form(None),
        start_date: Optional[date] = Form(None, description="Format: YYYY-MM-DD"),
        end_date: Optional[date] = Form(None, description="Format: YYYY-MM-DD"),
        budget: Optional[float] = Form(None),
        budget_currency: Optional[Literal["NGN", "USD"]] = Form(None),
        status: Optional[Literal["Active","Pending", "Draft"]] = Form(None),
        plan_id: Optional[UUID] = Form(None),
        preferred_inspection_days: Optional[List[WeekdayEnum]] = Form(None),
        preferred_inspection_window: Optional[InspectionWindowEnum] = Form(None),
        existing_image_ids: Optional[List[UUID]] = Form(None),
    ):
        self.name = name
        self.description = description
        self.project_type = project_type
        self.location_text = location_text
        self.location_map = location_map
        self.start_date = start_date
        self.end_date = end_date
        self.budget = budget
        self.budget_currency = budget_currency
        self.status = status
        self.plan_id = plan_id
        self.preferred_inspection_days = preferred_inspection_days
        self.preferred_inspection_window = preferred_inspection_window
        self.existing_image_ids = existing_image_ids