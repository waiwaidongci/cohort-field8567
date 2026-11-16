from enum import StrEnum
class Role(StrEnum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
class CampaignStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
FEATURES = ("recency", "frequency", "spend", "learning_days")
