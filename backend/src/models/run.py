from sqlalchemy import String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from src.config.database import Base
class SegmentRun(Base):
    __tablename__ = "segment_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    features: Mapped[list] = mapped_column(JSON)
    k_min: Mapped[int]
    k_max: Mapped[int]
    constraints: Mapped[dict | None] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
