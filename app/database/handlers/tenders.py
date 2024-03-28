from .. import models as db_models
from ..session import get_db_session

from app.api import models

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert


async def _add_tender_data_to_db(
    session: AsyncSession, 
    tender_model,
    tender: models.NonresidentialDataOut
) -> None:
    await session.execute(
        insert(tender_model).values(
            **tender.model_dump(),
        ).on_conflict_do_update(
            index_elements=[tender_model.tender_id],
            index_where=tender_model.tender_id == tender.tender_id,
            set_={**tender.model_dump()}
        )
    )


async def db_add_tenders(tender_model, tenders: dict[str, models.NonresidentialDataOut]) -> None:
    async with get_db_session() as session:
        for tender in tenders.values():
            await _add_tender_data_to_db(session, tender_model, tender)
        await session.commit()


async def db_get_tender_by_id(
    session: AsyncSession, 
    tender_id: str,
) -> models.NonresidentialDataOut | None:
    tender = await session.scalars(
        select(
            db_models.NonresidentialTenders,
        ).where(
            db_models.NonresidentialTenders.tender_id == tender_id
        )
    )
    res = tender.first()
    if res:
        return models.NonresidentialDataOut.model_validate(res)


async def db_get_tenders_by_ids(
    session: AsyncSession, 
    tenders_ids: list[str],
) -> list[models.NonresidentialDataOut] | None:
    tenders = select(
        db_models.NonresidentialTenders,
    ).where(
        db_models.NonresidentialTenders.tender_id.in_(tenders_ids)
    )
    tenders = (await session.scalars(tenders)).all()
    if tenders:
        return [models.NonresidentialDataOut.model_validate(tender) for tender in tenders]


async def db_get_tenders_by_address(
    session: AsyncSession, 
    address_ids: list[str],
) -> list[models.NonresidentialDataOut] | None:
    tenders = select(
        db_models.NonresidentialTenders,
    ).where(
        db_models.NonresidentialTenders.address.in_(address_ids)
    )
    tenders = (await session.scalars(tenders)).all()
    if tenders:
        return [models.NonresidentialDataOut.model_validate(tender) for tender in tenders]


async def db_delete_expired_tenders(
    session: AsyncSession, 
    tender_model,
) -> list[str]:
    res = await session.execute(
        delete(tender_model).where(tender_model.applications_enddate <= datetime.now()).returning(tender_model.tender_id)
    )
    return [tender_id[0] for tender_id in res]

