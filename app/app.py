import asyncio

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.v1.routes import router as v1_router
from app.src.parse.nonresidential_tenders import parse_nonresidential
from app.src.parse.parking_spaces_tenders import parse_parking_spaces
from app.database.initdb import init_db


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
    asyncio.create_task(parse_parking_spaces())
    yield


app = FastAPI(
    lifespan=lifespan,
    swagger_ui_parameters={"displayRequestDuration": True}
)
app.include_router(v1_router, prefix="/api")

