import json

from datetime import datetime
from dataclasses import dataclass
from typing import Annotated

from fastapi import (
    APIRouter, 
    Depends, 
    Query,
    status, 
)

from app.api import models
from app.database.session import get_db_session
from app.database.handlers.tenders import db_get_tenders_by_ids, db_get_tender_by_id
from app.redis_client import redis_client

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/tender/{tender_id}", status_code=status.HTTP_200_OK)
async def get_tender_data_by_id(tender_id: str) -> models.NonresidentialDataOut | None:
    """ 
    Возвращает тендер по ID.
    """
    async with redis_client.client() as conn:
        cached_tender = await conn.get(tender_id)
        if cached_tender:
            return models.NonresidentialDataOut.model_validate(json.loads(cached_tender))

    async with get_db_session() as session:
        return await db_get_tender_by_id(session, tender_id)


@router.get("/tenders", status_code=status.HTTP_200_OK)
async def get_tenders_by_ids(
    tenders_ids: Annotated[list[str] | None, Query()] = None
) -> list[models.TenderOut] | None:
    """ 
    Возвращает тендеры по ID.
    """
    rates_resp = {}
    async with get_db_session() as session:
        rates = await db_get_tenders_by_ids(
            session, 
            tenders_ids,
        )
        rates_resp = rates
    return rates_resp


@router.delete("/tender", status_code=status.HTTP_200_OK)
async def delete_expired_tenders():
    ...
