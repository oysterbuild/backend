from typing import Literal, Optional, List
from uuid import UUID
from datetime import date, datetime, timezone
from pydantic import BaseModel, Field, model_validator
from enum import Enum
from schemas.enums import ReportType


# -------------------------------
# Request schema for creating/updating a report
# -------------------------------


class ReportImage(BaseModel):
    id: Optional[UUID] = Field(
        None, description="The ID of the image if already exists, else null"
    )
    image_url: Optional[str] = Field(
        None, description="The URL of the new image/video/file uploaded to cloud"
    )
    file_type: Optional[Literal["image", "file", "video"]] = Field(
        None, description="The type of file"
    )

    # @model_validator(mode="before")
    # def require_url_if_no_id(cls, v, values):
    #     if not v and not values.get("id"):
    #         raise ValueError("file_url must be provided if id is not present")
    #     return v


class ProjectReportRequest(BaseModel):
    title: Optional[str] = Field(
        None, max_length=225, description="Title of the report"
    )
    report_type: Optional[ReportType] = Field(..., description="Type of report")
    report_date: Optional[date] = Field(None, description="Date of the report")
    description: Optional[str] = Field(
        None, description="Detailed description of the report"
    )
    progress_percent: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Progress percentage"
    )
    recommendation: Optional[List[str]] = Field(
        None, max_length=255, description="Recommendation"
    )
    approval_required: Optional[bool] = Field(
        False, description="Whether approval is required"
    )
    approved: Optional[bool] = Field(
        False, description="Whether the report has been approved"
    )
    images: Optional[List[ReportImage]] = Field(
        None, description="List of images/videos/files uploaded"
    )

    @model_validator(mode="before")
    def check_dates(cls, values: dict) -> dict:
        now = datetime.now(timezone.utc).date()

        report_date = values.get("report_date")

        if isinstance(report_date, str):
            report_date = datetime.fromisoformat(report_date).date()
        elif isinstance(report_date, datetime):
            report_date = report_date.date()

        # Remove tzinfo if present
        if report_date and report_date < now:
            raise ValueError("start_date must not be in the past")

        return values


# -------------------------------
# Response schema for returning report data
# -------------------------------
class ProjectReportResponse(ProjectReportRequest):
    id: UUID = Field(..., description="Unique ID of the report")

    class Config:
        from_attributes = True  #


class UpdateProjectReportRequest(ProjectReportRequest):
    # existing_image_ids: Optional[List[UUID]] = []

    @model_validator(mode="before")
    def check_dates(cls, values: dict) -> dict:
        return values
