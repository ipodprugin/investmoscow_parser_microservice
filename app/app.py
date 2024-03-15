from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.v1.routes import router as v1_router
from app.database.initdb import init_db
from app.scheduled_tasks.parse import scheduler
from app.src.utils import clean_folder


@asynccontextmanager
async def lifespan(
    app: FastAPI
):
    clean_folder('/src/reports')
    clean_folder('/src/jsons')
    scheduler.start()
    for job in scheduler.get_jobs():
        job.modify(next_run_time=datetime.now())
    await init_db()
    yield


app = FastAPI(
    lifespan=lifespan,
    swagger_ui_parameters={"displayRequestDuration": True},
)
app.include_router(v1_router, prefix="/api")

