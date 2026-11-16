from sqlalchemy import String, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.config.database import Base
class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("dataset_id", "code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    code: Mapped[str] = mapped_column(String(80))
    recency: Mapped[float] = mapped_column(Float)
    frequency: Mapped[float] = mapped_column(Float)
    spend: Mapped[float] = mapped_column(Float)
    learning_days: Mapped[float] = mapped_column(Float)
