from app.redis_client import redis_client
from app.api import models


async def save_fields_to_redis(tenders_fields: dict[str, models.NonresidentialDataOut]):
    async with redis_client.client() as conn:
        for tender in tenders_fields.values():
            await conn.set(tender.tender_id, tender.model_dump_json())

