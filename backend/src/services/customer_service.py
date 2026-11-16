from fastapi import HTTPException
from sqlalchemy import select, func
from src.models import Customer, Dataset
from src.constants.enums import FEATURES
def list_customers(db, dataset_id, search, offset, limit):
    if not db.get(Dataset, dataset_id):
        raise HTTPException(404, "数据集不存在")
    query = select(Customer).where(Customer.dataset_id == dataset_id)
    if search:
        query = query.where(Customer.code.contains(search, autoescape=True))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Customer.id).offset(offset).limit(limit)).all()
    return {"total": total, "rows": [{"id": x.id, "code": x.code, **{f: getattr(x,f) for f in FEATURES}} for x in rows]}
