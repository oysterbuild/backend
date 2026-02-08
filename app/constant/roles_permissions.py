# core_perms/roles_perms.py
from . import permissions as p
from .roles import PROJECT_OWNER, REPORT_OFFICER

# ============================================================
# Project-level Role → Permission mapping
# ============================================================

default_role_permissions = [
    {
        "role": PROJECT_OWNER,
        "description": (
            "Full authority over a project. Can manage the project lifecycle, "
            "reports, updates, files, approvals, and dashboards."
        ),
        "permissions": [
            # # Dashboard access
            # p.CAN_ACCESS_PROJECT_DASHBOARD,
            # p.CAN_ACCESS_REPORT_DASHBOARD,
            # Project
            p.CAN_MANAGE_PROJECT,
            p.CAN_VIEW_PROJECT,  #
            # Reports
            p.CAN_MANAGE_REPORT,
            p.CAN_VIEW_REPORT,
            p.CAN_EXPORT_REPORT,
            # Updates
            p.CAN_SUBMIT_UPDATE,
            p.CAN_MANAGE_UPDATE,
            # Files / Documents
            p.CAN_MANAGE_FILES,
            # payment
            p.CAN_VIEW_PROJECT_PAYMENT,
            p.CAN_MANAGE_PROJECT_PAYMENT,
        ],
    },
    {
        "role": REPORT_OFFICER,
        "description": (
            "Handles project reporting and documentation. Can prepare reports, "
            "submit updates, upload evidence, and export reports, but has no "
            "approval or project control authority."
        ),
        "permissions": [
            # # Dashboard access
            # p.CAN_ACCESS_REPORT_DASHBOARD,
            # Reports
            p.CAN_MANAGE_REPORT,
            p.CAN_EXPORT_REPORT,
            # Updates
            p.CAN_SUBMIT_UPDATE,
            # Files / Evidence
            p.CAN_MANAGE_FILES,
        ],
    },
]
