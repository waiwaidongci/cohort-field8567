import time
from pathlib import Path
from redis import Redis
from sqlalchemy import select
from src.config.settings import REDIS_URL
from src.config.database import Session
from src.models import SegmentRun
from src.services.run_service import execute_run
redis=Redis.from_url(REDIS_URL)
# DB is authoritative: recover queued and interrupted runs after a worker restart.
while True:
    Path("/tmp/heartbeat").touch()
    with Session() as db:
        pending=db.scalar(select(SegmentRun).where(SegmentRun.status.in_(["queued","running"])).order_by(SegmentRun.id))
        if pending:
            execute_run(db,pending.id)
        else:
            redis.brpop("cohort:runs",timeout=2)
    time.sleep(.1)
