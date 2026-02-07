import enum


class ProjectType(enum.Enum):
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"
    INFRASTRUCTURE = "Infrastructure"


class ReportType(enum.Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MILESTONE = "Milestone Completion"
    INCIDENT = "Incident"


class PaymentStatus(enum.Enum):
    PENDING = "Pending"
    PAID = "Paid"
    APPROVED = "Approved"


class MilestoneStatus(enum.Enum):
    PENDING = "Pending"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    APPROVED = "Approved"


class InspectionWindowEnum(enum.Enum):
    Morning = "Morning"
    Afternoon = "Afternoon"
    Evening = "Evening"


class WeekdayEnum(enum.Enum):
    Monday = "Monday"
    Tuesday = "Tuesday"
    Wednesday = "Wednesday"
    Thursday = "Thursday"
    Friday = "Friday"
    Saturday = "Saturday"
    Sunday = "Sunday"
