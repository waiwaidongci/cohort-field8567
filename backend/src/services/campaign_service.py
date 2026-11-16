import csv
import io
from sqlalchemy import select
from fastapi import HTTPException
from src.models import Campaign, Segment, Customer
from src.constants.enums import FEATURES
def list_campaigns(db):
    return [{"id":c.id,"name":c.name,"segment_id":c.segment_id,"segment_name":s.name,"size":s.size,"note":c.note,"status":c.status,"created_at":c.created_at} for c,s in db.execute(select(Campaign,Segment).join(Segment,Campaign.segment_id==Segment.id).order_by(Campaign.id.desc())).all()]
def create_campaign(db, data):
    if not db.get(Segment,data.segment_id):
        raise HTTPException(404,"目标群组不存在")
    if db.scalar(select(Campaign).where(Campaign.name==data.name)):
        raise HTTPException(409,"方案名称已存在")
    item=Campaign(**data.model_dump(),status="draft"); db.add(item); db.commit(); return item
def approve_campaign(db, campaign_id):
    item=db.get(Campaign,campaign_id)
    if not item:
        raise HTTPException(404,"方案不存在")
    item.status="approved"; db.commit(); return item
def export_campaign(db,campaign_id):
    item=db.get(Campaign,campaign_id)
    if not item:
        raise HTTPException(404,"方案不存在")
    if item.status!="approved":
        raise HTTPException(409,"方案需先由运营负责人批准后才能交付名单")
    segment=db.get(Segment,item.segment_id)
    rows=db.scalars(select(Customer).where(Customer.id.in_(segment.customer_ids)).order_by(Customer.code)).all()
    out=io.StringIO(); out.write("\ufeff"); writer=csv.writer(out); writer.writerow(["code",*FEATURES,"segment","campaign"])
    def csv_text(value):
        return ("'"+value) if value.startswith(("=","+","-","@","\t","\r")) else value
    for row in rows:
        writer.writerow([csv_text(row.code),*[getattr(row,f) for f in FEATURES],csv_text(segment.name),csv_text(item.name)])
    return out.getvalue()
