import asyncio

from typing import Annotated
from enum import Enum
from fastapi import (
    APIRouter, 
    Query,
    status, 
)

from app.api import models
from app.api.v1.handlers import handler_delete_expired_tenders
from app.database.session import get_db_session
from app.database.handlers.tenders import (
    db_get_tenders_by_ids, 
    db_get_tenders_by_address,
    db_get_tender_by_id,
)

router = APIRouter(prefix="/v1", tags=["v1"])


class ByEnum(str, Enum):
    tender_id = 'tender_id'
    address = 'address'


@router.get("/tender/{tender_id}", status_code=status.HTTP_200_OK)
async def get_tender_data_by_id(tender_id: str) -> models.NonresidentialDataOut | None:
    """ 
    Возвращает тендер по ID.
    """
    async with get_db_session() as session:
        return await db_get_tender_by_id(session, tender_id)


@router.get("/tenders", status_code=status.HTTP_200_OK)
async def get_tenders_by_ids(
    params: Annotated[list[str], Query(description="List of tenders ids of addresses")],
    by: ByEnum,
) -> list[models.NonresidentialDataOut] | None:
    """ 
    Возвращает тендеры по ID или адресу.
    """
    async with get_db_session() as session:
        if by == ByEnum.tender_id.value:
            return await db_get_tenders_by_ids(
                session, 
                params,
            )
        return await db_get_tenders_by_address(
            session, 
            params,
        )


@router.delete("/tenders", status_code=status.HTTP_202_ACCEPTED)
async def delete_expired_tenders():
    asyncio.create_task(handler_delete_expired_tenders())

