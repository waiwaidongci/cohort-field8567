from fastapi import HTTPException
from sqlalchemy import select
from redis import Redis
from src.config.settings import REDIS_URL
from src.models import Dataset, SegmentRun, Customer, Segment
from src.services.clustering import cluster_customers
queue = Redis.from_url(REDIS_URL)
def list_runs(db):
    return db.scalars(select(SegmentRun).order_by(SegmentRun.id.desc())).all()
def create_run(db, data):
    if not db.get(Dataset, data.dataset_id):
        raise HTTPException(404,"数据集不存在")
    if db.scalar(select(SegmentRun).where(SegmentRun.name==data.name)):
        raise HTTPException(409,"实验名称已存在，请使用新的名称")
    run=SegmentRun(**data.model_dump(), status="queued")
    db.add(run); db.commit()
    queue.lpush("cohort:runs", str(run.id))
    return run
def execute_run(db, run_id):
    run=db.get(SegmentRun,run_id)
    if not run or run.status not in ("queued", "running"):
        return
    run.status="running"; db.commit()
    try:
        customers=db.scalars(select(Customer).where(Customer.dataset_id==run.dataset_id).order_by(Customer.id)).all()
        result, segments=cluster_customers(customers,run.features,run.k_min,run.k_max)
        for old in db.scalars(select(Segment).where(Segment.run_id==run.id)).all():
            db.delete(old)
        db.flush()
        db.add_all([Segment(run_id=run.id, **segment) for segment in segments])
        run.result=result; run.status="completed"; run.error=""; db.commit()
    except Exception as exc:
        db.rollback(); run=db.get(SegmentRun,run_id); run.status="failed"; run.error=str(exc)[:500]; db.commit()
def run_detail(db, run_id):
    run=db.get(SegmentRun,run_id)
    if not run:
        raise HTTPException(404,"分群实验不存在")
    return run
