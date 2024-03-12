from .. import models as db_models
from ..session import get_db_session

from app.api import models

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
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
    tender = select(
        db_models.NonresidentialTenders,
    ).where(
        db_models.NonresidentialTenders.tender_id == tender_id
    )
    tender = await session.execute(tender)
    if tender:
        return models.NonresidentialDataOut.model_validate(tender)


async def db_get_tenders_by_ids(
    session: AsyncSession, 
    tenders_ids: list[str] | None = None,
) -> list[models.TenderOut] | None:
    tenders = select(
        db_models.NonresidentialTenders,
    ).where(
        db_models.NonresidentialTenders.tender_id in tenders_ids if tenders_ids else True,
    )
    tenders = await session.execute(tenders)
    if tenders:
        return [models.TenderOut.model_validate(tender) for tender in tenders]

