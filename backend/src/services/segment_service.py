from sqlalchemy import select
from src.models import Segment, SegmentRun
from fastapi import HTTPException
def list_segments(db, run_id=None):
    query=select(Segment)
    if run_id is not None:
        if not db.get(SegmentRun,run_id):
            raise HTTPException(404,"分群实验不存在")
        query=query.where(Segment.run_id==run_id)
    return db.scalars(query.order_by(Segment.run_id.desc(),Segment.label)).all()
