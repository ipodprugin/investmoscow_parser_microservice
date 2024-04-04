import pandas as pd

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
    tender: models.NonresidentialDataDB
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


async def db_add_tenders(tender_model, tenders: dict[str, models.NonresidentialDataDB]) -> None:
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


def pandas_query(session, db_model):
  conn = session.connection()
  query = select(db_model)
  return pd.read_sql_query(query, conn)


from sqlalchemy import text

async def db_get_all_tenders_of_type_as_pandas_df(
    session: AsyncSession, 
    db_model,
):
    sql = text(
        f"select column_name, col_description('public.{db_model.__tablename__}'::regclass, ordinal_position) "
        "from information_schema.columns "
        f"where table_schema = 'public' and table_name = '{db_model.__tablename__}';"
    )
    columns_descriptions = await session.execute(sql)
    columns_descriptions = columns_descriptions.all()
    table_headers_for_rename = {old_name: new_name for old_name, new_name in columns_descriptions}
    df = await session.run_sync(pandas_query, db_model=db_model)
    df = df.rename(columns=table_headers_for_rename)
    return df

