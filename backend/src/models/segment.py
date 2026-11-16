from sqlalchemy import String, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.config.database import Base
class Segment(Base):
    __tablename__ = "segments"
    __table_args__ = (UniqueConstraint("run_id", "label"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("segment_runs.id"))
    label: Mapped[int]
    name: Mapped[str] = mapped_column(String(100))
    size: Mapped[int]
    center: Mapped[dict] = mapped_column(JSON)
    customer_ids: Mapped[list] = mapped_column(JSON)
    recommendation: Mapped[str] = mapped_column(String(500))
