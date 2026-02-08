# core_perms/permissions.py

# ============================================================
# Project Permissions (applies to Project Owner & Report Officer)
# ============================================================

# ---------------------------
# Dashboard access
# ---------------------------
CAN_ACCESS_PROJECT_DASHBOARD = "CAN_ACCESS_PROJECT_DASHBOARD"
CAN_ACCESS_REPORT_DASHBOARD = "CAN_ACCESS_REPORT_DASHBOARD"

# ---------------------------
# Project
# ---------------------------
CAN_MANAGE_PROJECT = "CAN_MANAGE_PROJECT"
# create / update / delete project details

CAN_VIEW_PROJECT = "CAN_VIEW_PROJECT"
# approve project milestones, closures, or key actions

CAN_MANAGE_PROJECT_PAYMENT = "CAN_MANAGE_PROJECT_PAYMENT"
CAN_VIEW_PROJECT_PAYMENT = "CAN_VIEW_PROJECT_PAYMENT"
# ---------------------------
# Reports
# ---------------------------
CAN_MANAGE_REPORT = "CAN_MANAGE_REPORT"
# create / update / delete reports

CAN_VIEW_REPORT = "CAN_VIEW_REPORT"
# approve submitted reports

CAN_EXPORT_REPORT = "CAN_EXPORT_REPORT"
# export reports (PDF, CSV, etc.)

# ---------------------------
# Site / Project Updates
# ---------------------------
CAN_SUBMIT_UPDATE = "CAN_SUBMIT_UPDATE"
# submit progress or site updates (no edit/delete after submission)

CAN_MANAGE_UPDATE = "CAN_MANAGE_UPDATE"
# edit / delete updates (Project Owner only)

# ---------------------------
# Files / Evidence / Documents
# ---------------------------
CAN_MANAGE_FILES = "CAN_MANAGE_FILES"
# upload / edit / delete files, photos, documents
