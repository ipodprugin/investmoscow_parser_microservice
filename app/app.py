import asyncio
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.api.v1.routes import router as v1_router
from app.src.parse.nonresidential_tenders import parse_nonresidential
from app.src.parse.parking_spaces_tenders import parse_parking_spaces
from app.database.initdb import init_db
from app.config import settings


logging.basicConfig(
    filename='./app/app.log',
    format='%(asctime)s - %(process)s - %(name)s:%(lineno)d - %(levelname)s -'
    ' %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    app: FastAPI
):
    scheduler.start()

    search_fields = [
        'Тип входа',
        'Наличие окон и их размер',
        'Высота потолков, м',
        'Округ города Москвы',
        'Муниципальный район',
    ]

    await init_db()
    asyncio.create_task(parse_nonresidential(search_fields))
    asyncio.create_task(parse_parking_spaces())
    yield


app = FastAPI(
    lifespan=lifespan,
    swagger_ui_parameters={"displayRequestDuration": True}
)
scheduler = AsyncIOScheduler()


@scheduler.scheduled_job('interval', hours=5)
async def example_heartbeat():
    print('jfkdsl')
    logger.info('Time: !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! interval task is run...')


app.include_router(v1_router, prefix="/api")

