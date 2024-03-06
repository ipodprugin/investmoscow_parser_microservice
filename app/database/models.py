from datetime import datetime
from sqlalchemy import (
    String,
    Float,
    DateTime,
    ARRAY,
    orm
)


class Base(orm.DeclarativeBase):
    pass


class Tenders(Base):

    __tablename__ = "tenders"

    tender_id: orm.Mapped[str] = orm.mapped_column(String, primary_key=True)

    address: orm.Mapped[str] = orm.mapped_column(String, nullable=False)
    region_name: orm.Mapped[str] = orm.mapped_column(String, nullable=True)
    district_name: orm.Mapped[str] = orm.mapped_column(String, nullable=True)
    subway_stations: orm.Mapped[str] = orm.mapped_column(String, nullable=True)

    object_area: orm.Mapped[float] = orm.mapped_column(Float, nullable=False)
    deposit: orm.Mapped[float] = orm.mapped_column(Float, nullable=True)
    start_price: orm.Mapped[float] = orm.mapped_column(Float, nullable=True)
    m1_start_price: orm.Mapped[float] = orm.mapped_column(Float, nullable=True)
    min_price: orm.Mapped[float] = orm.mapped_column(Float, nullable=True)
    m1_min_price: orm.Mapped[float] = orm.mapped_column(Float, nullable=True)
    procedure_form: orm.Mapped[str] = orm.mapped_column(String, nullable=True)
    auction_step: orm.Mapped[float] = orm.mapped_column(Float, nullable=True)
    price_decrease_step: orm.Mapped[float] = orm.mapped_column(Float, nullable=True)

    applications_enddate: orm.Mapped[datetime] = orm.mapped_column(DateTime, nullable=True)
    tendering: orm.Mapped[datetime] = orm.mapped_column(DateTime, nullable=True)

    entrance_type: orm.Mapped[str] = orm.mapped_column(String, nullable=True)
    windows: orm.Mapped[str] = orm.mapped_column(String, nullable=True)
    ceilings: orm.Mapped[str] = orm.mapped_column(String, nullable=True)
    floor: orm.Mapped[str] = orm.mapped_column(String, nullable=True)

    lat: orm.Mapped[float] = orm.mapped_column(Float, nullable=True)
    lon: orm.Mapped[float] = orm.mapped_column(Float, nullable=True)

    images_links: orm.Mapped[list[str]] = orm.mapped_column(ARRAY(String), nullable=True)

