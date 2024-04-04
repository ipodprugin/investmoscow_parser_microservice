import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.logger import logger
from app.config import settings

from app.src.parse.nonresidential_tenders import parse_nonresidential
from app.src.parse.parking_spaces_tenders import parse_parking_spaces

from app.api.v1.handlers import handler_delete_expired_tenders, update_google_sheet_data

from app.api import models
from app.database import models as db_models


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


@scheduler.scheduled_job('interval', hours=6)
async def update_google_sheet():
    logger.info('Updating google sheet')

    models_mapping = {
        settings.NONRESIDENTIAL_WORKSHEET_TITLE: {
            'db_model': db_models.NonresidentialTenders, 
        },
        settings.PARKING_SPACES_WORKSHEET_TITLE: {
            'db_model': db_models.ParkingSpacesTenders, 
        },
    }

    for worksheet in (settings.NONRESIDENTIAL_WORKSHEET_TITLE, settings.NONRESIDENTIAL_WORKSHEET_TITLE ):
        asyncio.create_task(
            update_google_sheet_data(
                models_mapping[worksheet]['db_model'], 
                worksheet,
            )
        )

