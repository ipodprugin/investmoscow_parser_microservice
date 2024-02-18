from . import models as db_models
from ..api import models

from .session import get_db_session

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert


async def _add_tender_data_to_db(
    session: AsyncSession, 
    tender: models.NonresidentialDataOut
) -> None:
    await session.execute(
        insert(db_models.Tenders).values(
            **tender.model_dump(),
        ).on_conflict_do_update(
            index_elements=[db_models.Tenders.tender_id],
            index_where=db_models.Tenders.tender_id == tender.tender_id,
            set_={**tender.model_dump()}
        )
    )


async def add_tenders_to_db(tenders: dict[str, models.NonresidentialDataOut]) -> None:
    async with get_db_session() as session:
        for tender in tenders.values():
            await _add_tender_data_to_db(session, tender)
        await session.commit()


async def db_get_tender_by_id(
    session: AsyncSession, 
    tender_id: str,
) -> models.NonresidentialDataOut | None:
    # tenders = await session.scalars(
    tender = select(
        db_models.Tenders,
    ).where(
        db_models.Tenders.tender_id == tender_id
    )
    # )
    # tender = tenders.first()
    tender = await session.execute(tender)
    print('tender', tender)
    if tender:
        return models.NonresidentialDataOut.model_validate(tender)


async def db_get_tenders_by_ids(
    session: AsyncSession, 
    tenders_ids: list[str] | None = None,
) -> list[models.TenderOut] | None:
    tenders = select(
        db_models.Tenders,
    ).where(
        db_models.Tenders.tender_id in tenders_ids if tenders_ids else True,
    )
    tenders = await session.execute(tenders)
    if tenders:
        return [models.TenderOut.model_validate(tender) for tender in tenders]

