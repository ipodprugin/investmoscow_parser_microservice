import asyncio

from app.logger import logger
from app.config import settings
from app.src.parse.nonresidential_tenders import parse_nonresidential
from app.src.parse.parking_spaces_tenders import parse_parking_spaces
from app.api.v1.handlers import handler_delete_expired_tenders

from apscheduler.schedulers.asyncio import AsyncIOScheduler


scheduler = AsyncIOScheduler()


@scheduler.scheduled_job('interval', hours=5)
async def parse_nonresidential_task():
    logger.info('Starting parse_nonresidential_task')
    asyncio.create_task(parse_nonresidential(settings.SEARCH_FIELDS ))


@scheduler.scheduled_job('interval', hours=5)
async def parse_parking_spaces_task():
    logger.info('Starting parse_parking_spaces_task')
    asyncio.create_task(parse_parking_spaces())


@scheduler.scheduled_job('interval', hours=12)
async def delete_expired_tenders_task():
    asyncio.create_task(handler_delete_expired_tenders())

