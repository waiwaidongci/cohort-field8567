import csv
import io
from fastapi import HTTPException
from sqlalchemy import select, func
from src.models import Dataset, Customer
from src.schemas.customer import CustomerRow
from pydantic import ValidationError
def list_datasets(db):
    rows = db.execute(select(Dataset, func.count(Customer.id)).outerjoin(Customer, Customer.dataset_id == Dataset.id).group_by(Dataset.id)).all()
    return [{"id": d.id, "name": d.name, "source_file": d.source_file, "description": d.description, "row_count": n, "created_at": d.created_at} for d,n in rows]
def import_dataset(db, data):
    if db.scalar(select(Dataset).where(Dataset.name == data.name)):
        raise HTTPException(409, "数据集名称已存在")
    try:
        reader = csv.DictReader(io.StringIO(data.csv_text))
        rows = [CustomerRow.model_validate(row) for row in reader]
    except (ValidationError, ValueError, csv.Error) as exc:
        raise HTTPException(422, f"CSV 校验失败：{str(exc)[:250]}")
    if not 10 <= len(rows) <= 5000:
        raise HTTPException(422, "每个数据集需要 10–5000 行")
    if len({x.code for x in rows}) != len(rows):
        raise HTTPException(422, "客户匿名编号不能重复")
    d = Dataset(name=data.name, source_file=data.source_file, description=data.description)
    db.add(d); db.flush()
    db.add_all([Customer(dataset_id=d.id, **r.model_dump()) for r in rows]); db.commit()
    return {"id": d.id, "row_count": len(rows)}
