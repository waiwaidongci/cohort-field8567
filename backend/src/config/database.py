from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from src.config.settings import DATABASE_URL
class Base(DeclarativeBase):
    pass
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)
def ensure_schema_upgrades():
    # 幂等应用版本迁移，对应 migrations/002_segment_run_constraints.sql；
    # 旧库补列后历史实验与获批名单保持原结果，新列默认为 NULL（无约束）。
    with engine.begin() as conn:
        columns = {column["name"] for column in inspect(conn).get_columns("segment_runs")}
        if "constraints" not in columns:
            conn.execute(text("ALTER TABLE segment_runs ADD COLUMN constraints JSON NULL"))
def get_db():
    with Session() as db:
        yield db
