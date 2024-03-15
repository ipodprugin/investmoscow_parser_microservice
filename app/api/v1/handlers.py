import aiohttp

from app.database.session import get_db_session
from app.database import models as db_models
from app.database.handlers.tenders import db_delete_expired_tenders
from app.src.images import del_folder
from app.config import settings
from app.logger import logger


async def handler_delete_expired_tenders():
    logger.info('Started deleting expired tenders')
    async with get_db_session() as session:
        nonresidential_tenders_ids = await db_delete_expired_tenders(
            session,
            db_models.NonresidentialTenders
        )
        parking_spaces_tenders_ids = await db_delete_expired_tenders(
            session,
            db_models.ParkingSpacesTenders
        )

    DISK_AUTH_HEADERS = {'accept': 'application/json', 'Authorization': 'OAuth %s' % settings.YADISK_OAUTH_TOKEN}
    async with aiohttp.ClientSession(headers=DISK_AUTH_HEADERS) as session:
        await del_folder(
            session=session,
            basefolder=settings.NONRESIDENTIAL_FOLDERNAME,
            tenders_ids=nonresidential_tenders_ids
        )
        await del_folder(
            session=session,
            basefolder=settings.PARKING_SPACES_FOLDERNAME,
            tenders_ids=parking_spaces_tenders_ids
        )
    logger.info(f'Deleted expired tenders:\nnonresidential: {nonresidential_tenders_ids}\nparking_spaces: {parking_spaces_tenders_ids}')

