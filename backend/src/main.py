import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from redis import Redis
from src.config.database import Base,engine
from src.config.settings import SEED_DEMO,REDIS_URL
from src import models
from src.routes import auth,datasets,customers,runs,segments,campaigns,audit
from src.middlewares.audit import AuditMiddleware
from src.middlewares.errors import ErrorMiddleware
from src.middlewares.rate_limit import RateLimitMiddleware
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    if SEED_DEMO:
        try:
            from scripts.seed_demo import seed
            seed()
        except Exception:
            logging.exception("seed failed; application remains available")
    yield
app=FastAPI(title="苇岸客户留存分群",lifespan=lifespan)
app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ErrorMiddleware)
for router in (auth,datasets,customers,runs,segments,campaigns,audit):
    app.include_router(router.router)
@app.get("/health")
def health():
    with engine.connect() as conn: conn.execute(text("SELECT 1"))
    Redis.from_url(REDIS_URL).ping()
    return {"status":"ok"}
