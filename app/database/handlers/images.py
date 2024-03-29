from ..session import get_db_session

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession


async def db_add_images_links(tender_model, images_links: dict[str, list[str]]) -> None:
    async with get_db_session() as session:
        for tender_id, links in images_links.items():
            await _db_add_tender_images_links(session, tender_model, tender_id, links)
        await session.commit()


async def _db_add_tender_images_links(
    session: AsyncSession, 
    tender_model,
    tender_id: str,
    images_links: list[str],
) -> None:
    await session.execute(
        update(tender_model)
        .where(tender_model.tender_id == tender_id)
        .values(images_links=images_links)
    )


