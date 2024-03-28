import asyncio
import aiohttp

from app.api import models

from app.config import settings
from app.logger import logger

from app.database.handlers.tenders import db_add_tenders

from app.src.pdf import search_fields_in_pdf
from app.src.utils import delete_files
from app.src.images import process_images
from app.src.tenders import (
    get_tender,
    get_tenders,
    get_evaluation_report_link,
)

from app.database import models as dbmodels


async def find_fields(tender_ids: list[str], search_fields: list[str]):
    result = {}
    for tender_id in tender_ids:
        path = f'/src/reports/{tender_id}.pdf'
        found = await search_fields_in_pdf(path, search_fields)
        result[tender_id] = (models.TenderDataFromFilesPayload.model_validate(found))
    return result


async def download_doc_by_link(url: str, path: str, session: aiohttp.ClientSession):
    async with session.get(url) as response:
        with open(path, 'wb') as fd:
            async for chunk in response.content.iter_chunked(2048):
                fd.write(chunk)


async def download_reports(tender_links: dict[str, str], session: aiohttp.ClientSession):
    for tender_id, link in tender_links.items():
        path = f'/src/reports/{tender_id}.pdf'
        await download_doc_by_link(
            link, 
            path,
            session
        )


# TODO: make checker that tender exists in db
async def _parse_nonresidential(
    tenders_ids: list[str], 
    search_fields: list[str]
) -> dict:
    file_data = {}
    tenders = {}
    tenders_images = []
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=settings.SSL)) as session:
        for tender_id in tenders_ids:
            data = await get_tender(session, tender_id)
            tender = models.NonresidentialDataValidate.model_validate(data)
            tenders[tender_id] = tender

            images = tender.image_info.model_dump()
            images['tender_id'] = tender.tender_id
            tenders_images.append(images)

            evaluation_report_link = await get_evaluation_report_link(data)
            if evaluation_report_link:
                file_data[tender_id] = evaluation_report_link
            else:
                logger.error(f"can't get evaluation report link for tender {tender_id}")
        await download_reports(file_data, session)

    file_data = await find_fields(tender_ids=list(file_data.keys()), search_fields=search_fields)
    for tender_id, tender in tenders.items():
        _file_data = file_data.get(tender_id)
        tenders[tender_id] = models.NonresidentialDataOut(
            tender_id=str(tender.tender_id),
            investmoscow_url=tender.investmoscow_url,
            address=tender.header_info.address,
            subway_stations=tender.header_info.subway[0].subwayStationName if tender.header_info.subway else None,
            object_area=tender.object_area,
            floor=tender.floor,
            applications_enddate=tender.applications_enddate,
            deposit=tender.deposit,
            start_price=tender.start_price,
            m1_start_price=tender.m1_start_price,
            min_price=tender.min_price,
            m1_min_price=tender.m1_min_price,
            procedure_form=tender.form,
            auction_step=tender.auction_step,
            price_decrease_step=tender.price_decrease_step,
            tendering=tender.tendering,
            lat=tender.map_info.coords.lat,
            lon=tender.map_info.coords.lon,
            entrance_type=_file_data.entrance_type if _file_data else None,
            windows=_file_data.windows if _file_data else None,
            ceilings=_file_data.ceilings if _file_data else None,
            region_name=_file_data.region_name if _file_data else None,
            district_name=_file_data.district_name if _file_data else None,
        )
        print(tenders[tender_id])

    asyncio.create_task(db_add_tenders(dbmodels.NonresidentialTenders, tenders))

    return {'images': tenders_images}


async def parse_nonresidential(
    search_fields: list[str]
):
    # TODO: save parsing progress on shutdown to avoid reparse on restart
    # TODO: implement autoremove tenders from db that term expired
    pagenumber = settings.PAGENUMBER
    while True:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=settings.SSL)) as session:
                tenders = await get_tenders(
                    session, 
                    pagenumber, 
                    settings.PAGESIZE, 
                    models.TenderTypes.nonresidential.value
                )
            entities = tenders.get('entities')
            if not entities:
                logger.info('Ended parsing nonresidential tenders.')
                return
            else:
                logger.info(f'got nonresidential tenders on {pagenumber = } with {settings.PAGESIZE = }')
                tender = None

                for entity in entities:
                    try:
                        tenders = entity.get('tenders')
                        tenders_ids = []
                        for tender in tenders:
                            if _id := tender.get('id'):
                                tenders_ids.append(str(_id))
                            else:
                                logger.error('No id in tender', tender)
                        tenders_images = await _parse_nonresidential(tenders_ids, search_fields)
                        tenders_images = models.TenderImages(**tenders_images)
                        asyncio.create_task(
                            process_images(
                                basefolder=settings.NONRESIDENTIAL_FOLDERNAME,
                                tender_model=dbmodels.NonresidentialTenders,
                                tenders_images=tenders_images, 
                                tenders_ids=tenders_ids.copy()
                            )
                        )
                        delete_files(
                            folder='/src/reports',
                            filesnames=tenders_ids,
                            extension='.pdf'
                        )
                        delete_files(
                            folder='/src/jsons',
                            filesnames=tenders_ids,
                            extension='.json'
                        )
                    except Exception as e:
                        logger.exception(f'Exception while parsing {tender}')
                pagenumber += 1
                await asyncio.sleep(60 * 5)
        except Exception as e:
            logger.exception(f'Exception while parsing')
            await asyncio.sleep(60)

