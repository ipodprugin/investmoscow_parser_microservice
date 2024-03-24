from app.config import settings
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)


engine = create_async_engine(settings.DB_URL)
factory = async_sessionmaker(engine)

