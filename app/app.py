import traceback
import aiohttp
import asyncio
import uvicorn

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings

from .api import models
from .api.v1.routes import router as v1_router

from .src.pdf import search_fields_in_pdf
from .src.utils import clean_folder
from .src.tenders import (
    get_tender, 
    get_tenders, 
    get_evaluation_report_link, 
)

from .database.helpers import add_tenders_to_db
from .database.initdb import init_db
from .redis_client import redis_client


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


async def save_fields_to_redis(tenders_fields: dict[str, models.NonresidentialDataOut]):
    async with redis_client.client() as conn:
        for tender in tenders_fields.values():
            await conn.set(tender.tender_id, tender.model_dump_json())


# TODO: make checker that tender exists in db
async def _parse_nonresidential(
    tenders_ids: list[str], 
    search_fields: list[str]
):
    print('tenders_ids', tenders_ids)
    file_data = {}
    tenders = {}
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=settings.SSL)) as session:
        for tender_id in tenders_ids:
            data = await get_tender(session, tender_id)
            tender = models.NonresidentialDataValidate.model_validate(data)
            tenders[tender_id] = tender

            evaluation_report_link = await get_evaluation_report_link(data)
            if evaluation_report_link:
                file_data[tender_id] = evaluation_report_link
            else:
                print(f"can't get evaluation report link for tender {tender_id}")
        await download_reports(file_data, session)

    # TODO: refactor list(result.keys())
    file_data = await find_fields(tender_ids=list(file_data.keys()), search_fields=search_fields)
    for tender_id, tender in tenders.items():
        _file_data = file_data.get(tender_id)
        tenders[tender_id] = models.NonresidentialDataOut(
            tender_id=str(tender.tender_id),
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

    asyncio.create_task(save_fields_to_redis(tenders))
    asyncio.create_task(add_tenders_to_db(tenders))


async def parse_nonresidential(
    search_fields: list[str]
):
    # TODO: save parsing progress on shutdown to avoid reparse on restart
    while True:
        try:
            print('SSL', settings.SSL)
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=settings.SSL)) as session:
                tenders = await get_tenders(
                    session, 
                    settings.PAGENUMBER, 
                    settings.PAGESIZE, 
                    models.TenderTypes.nonresidential.value
                )
                print('GOT TENDERS')
            entities = tenders.get('entities')
            for entity in entities:
                tenders = entity.get('tenders')
                tenders_ids = []
                for tender in tenders:
                    if _id := tender.get('id'):
                        tenders_ids.append(str(_id))
                    else:
                        print('-------- ERROR: no id in tender', tender)
                await _parse_nonresidential(tenders_ids, search_fields)
                clean_folder('/src/reports')
                clean_folder('/src/jsons')
            print('parsed nonresidential tenders')
            print('SLEEP')
            await asyncio.sleep(60 * 60)
        except Exception:
            traceback.print_exc()
            await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(
    app: FastAPI
):
    search_fields = [
        'Тип входа',
        'Наличие окон и их размер',
        'Высота потолков, м',
        'Округ города Москвы',
        'Муниципальный район',
    ]

    await init_db()
    asyncio.create_task(parse_nonresidential(search_fields))
    yield


app = FastAPI(
    lifespan=lifespan,
    swagger_ui_parameters={"displayRequestDuration": True}
)
app.include_router(v1_router, prefix="/api")

