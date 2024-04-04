import aiohttp
import pygsheets

from app.logger import logger
from app.config import settings
from app.src.images import del_folder

from app.database import models as db_models
from app.database.session import get_db_session
from app.database.handlers.tenders import (
    db_delete_expired_tenders, 
    db_get_all_tenders_of_type_as_pandas_df,
    db_get_table_columns_descriptions,
)


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


async def update_google_sheet_data(db_model, worksheet):
    try:
        logger.info('connecting to GSheets...')
        sa = pygsheets.authorize(service_file=settings.GSHEETS_CREDS_PATH)
        logger.info('Opening gsheet by url...')
        sh = sa.open_by_url(settings.GSHEETURL)
        worksheet = sh.worksheet_by_title(worksheet)

        async with get_db_session() as session:
            table_headers_for_rename = await db_get_table_columns_descriptions(session, db_model)
            table_pandas_df = await db_get_all_tenders_of_type_as_pandas_df(session, db_model)

        for index, row in table_pandas_df.iterrows():
            # Для автоматической выгрузки на авито, ссылки на фото для каждого объявления
            # должны быть записаны в одной ячейке через разделитель " | ".
            links = row['images_links']
            table_pandas_df.loc[index, 'images_links'] = ' | '.join(links) if bool(links) else ''

        table_pandas_df = table_pandas_df.rename(columns=table_headers_for_rename)

        worksheet.clear()
        logger.info(f'Cleared worksheet "{worksheet}"')

        worksheet.set_dataframe(
            table_pandas_df,
            start='A1', 
            nan='',
            copy_head=True,
            escape_formulae=True
        )
        logger.info(f'Updated worksheet "{worksheet}"')
        return True
    except Exception as e:
        logger.exception(f'Exception while updating worksheet "{worksheet}"')
        return False

