import random
import json
from sqlalchemy import select,func
from src.config.database import Base, engine, Session, ensure_schema_upgrades
from src.models import User,Dataset,Customer,SegmentRun,Segment,Campaign
from src.utils.security import hash_password
from src.services.run_service import execute_run

def seed():
    Base.metadata.create_all(engine)
    ensure_schema_upgrades()
    rng=random.Random(42)
    with Session() as db:
        for role,name in [("admin","沈苇 · 运营负责人"),("analyst","陈岸 · 研究员"),("viewer","林禾 · 内容经理")]:
            if not db.scalar(select(User).where(User.email==f"{role}@weian.demo")):
                db.add(User(email=f"{role}@weian.demo",name=name,role=role,password_hash=hash_password("Weian2026!")))
        dataset=db.scalar(select(Dataset).where(Dataset.name=="苇岸学习社 · 近90天会员特征"))
        if not dataset:
            dataset=Dataset(name="苇岸学习社 · 近90天会员特征",source_file="wei-an-members-202611.csv",description="720 位匿名学习者；消费与学习活跃按同一观察日汇总，金额单位为元。")
            db.add(dataset);db.flush()
            centers=[(9,14,1480,24),(76,9,1260,3),(31,3,260,7),(37,7,720,14)]
            for i in range(720):
                center=centers[i%4]
                vals=[max(0,round(rng.gauss(v,max(1,v*.13)),2)) for v in center]
                db.add(Customer(dataset_id=dataset.id,code=f"WA-{i+1:04d}",recency=vals[0],frequency=vals[1],spend=vals[2],learning_days=vals[3]))
        db.commit()
        for name,features,kmin,kmax in [("11月留存基线",["recency","frequency","spend","learning_days"],2,6),("消费与近期活跃对照",["recency","spend"],2,5),("学习深度复核",["frequency","learning_days","spend"],2,5)]:
            if not db.scalar(select(SegmentRun).where(SegmentRun.name==name)):
                run=SegmentRun(name=name,dataset_id=dataset.id,features=features,k_min=kmin,k_max=kmax,status="queued")
                db.add(run);db.commit();execute_run(db,run.id)
        first=db.scalar(select(SegmentRun).where(SegmentRun.name=="11月留存基线"))
        silent=db.scalar(select(Segment).where(Segment.run_id==first.id,Segment.name=="沉默高价值"))
        if silent:
            for name,status in [("冬季复学关怀","approved"),("课程进度回顾试点","draft")]:
                if not db.scalar(select(Campaign).where(Campaign.name==name)):
                    db.add(Campaign(name=name,segment_id=silent.id,note="以学习进度回顾为起点，14 天后观察复学表现；名单仅含匿名编号。",status=status))
        db.commit()
        counts={table.__tablename__:db.scalar(select(func.count()).select_from(table)) for table in (User,Dataset,Customer,SegmentRun,Segment,Campaign)}
        print(json.dumps(counts,ensure_ascii=False))
if __name__=="__main__":
    seed()
