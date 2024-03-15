import asyncio
import aiohttp

from app.api import models

from app.config import settings
from app.logger import logger

from app.database.handlers.tenders import db_add_tenders

from app.src.utils import delete_files
from app.src.images import process_images
from app.src.tenders import (
    get_tender,
    get_tenders,
    find_smallest_area_tender
)

from app.database import models as dbmodels

async def _parse_parking_spaces(
    tenders_ids: list[str],
    object_address: str, 
    region_name: str,
    district_name : str,
    count: int,
) -> dict:
    tenders = {}
    tenders_images = []
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=settings.SSL)) as session:
        for tender_id in tenders_ids:
            data = await get_tender(session, tender_id)
            tender = models.ParkingSpacesDataValidate.model_validate(data)
            tenders[tender_id] = tender

            images = tender.image_info.model_dump()
            images['tender_id'] = tender.tender_id
            tenders_images.append(images)

            tenders[tender_id] = models.ParkingSpacesDataOut(
                tender_id=str(tender.tender_id),
                investmoscow_url=tender.investmoscow_url,
                address=object_address,
                object_area=tender.object_area,
                floor=tender.floor,
                applications_enddate=tender.applications_enddate,
                deposit=tender.deposit,
                start_price=tender.start_price,
                region_name=region_name,
                district_name=district_name,
                procedure_form=tender.form,
                parking_type=tender.parking_type,
                parking_place=tender.parking_place,
                subway_stations=tender.header_info.subway[0].subwayStationName if tender.header_info.subway else None,
                count=count,
            )

    asyncio.create_task(db_add_tenders(dbmodels.ParkingSpacesTenders, tenders))
    return {'images': tenders_images}


async def parse_parking_spaces():
    pagenumber = settings.PAGENUMBER
    tenders_ids = []
    while True:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=settings.SSL)) as session:
                tenders = await get_tenders(
                    session, 
                    pagenumber, 
                    settings.PAGESIZE, 
                    models.TenderTypes.parking_space.value
                )
            entities = tenders.get('entities')
            if not entities:
                logger.info('Ended parsing parking spaces tenders.')
                return
            else:
                logger.info(f'got parking spaces tenders on {pagenumber = } with {settings.PAGESIZE = }')
                tender = None
                for entity in entities:
                    object_address = entity['objectAddress']
                    try:
                        tenders = entity.get('tenders')
                        if tenders:
                            count = entity.get('count')

                            tender_index = 0
                            if count > 1:
                                tender_index = find_smallest_area_tender(tenders)

                            tender = tenders[tender_index]
                            region_name = tender['regionName']
                            district_name = tender['districtName']
                            _id = str(tender.get('id'))
                            tenders_ids.append(_id)
                            tenders_images = await _parse_parking_spaces(
                                [_id],
                                object_address, 
                                region_name,
                                district_name,
                                count,
                            )
                            tenders_images = models.TenderImages(**tenders_images)
                            asyncio.create_task(
                                process_images(
                                    basefolder=settings.PARKING_SPACES_FOLDERNAME,
                                    tender_model=dbmodels.ParkingSpacesTenders,
                                    tenders_images=tenders_images, 
                                    tenders_ids=[_id], 
                                )
                            )
                            # clean_folder('/src/reports')
                            # clean_folder('/src/jsons')
                    except Exception as e:
                        logger.exception(f'Exception while parsing {tender}')
                pagenumber += 1
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
                await asyncio.sleep(60 * 5)
        except Exception as e:
            logger.exception(f'Exception while parsing')
            await asyncio.sleep(60)

