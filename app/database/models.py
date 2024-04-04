from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy import (
    String,
    Float,
    Integer,
    DateTime,
    ARRAY,
    orm
)


class Base(AsyncAttrs, orm.DeclarativeBase):
    pass


class NonresidentialTenders(Base):

    __tablename__ = "nonresidential_tenders"

    tender_id: orm.Mapped[str] = orm.mapped_column(String, primary_key=True, comment="ID тендера")
    investmoscow_url: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Сылка на investmoscow")

    address: orm.Mapped[str] = orm.mapped_column(String, nullable=False, comment="Адрес")
    region_name: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Округ")
    district_name: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Район")
    subway_stations: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Метро")

    object_area: orm.Mapped[float] = orm.mapped_column(Float, nullable=True, comment="Площадь")
    deposit: orm.Mapped[float] = orm.mapped_column(Float, nullable=True, comment="Задаток")
    start_price: orm.Mapped[float] = orm.mapped_column(Float, nullable=True, comment="Начальная цена")
    m1_start_price: orm.Mapped[float] = orm.mapped_column(Float, nullable=True, comment="")
    min_price: orm.Mapped[float] = orm.mapped_column(Float, nullable=True, comment="Минимальная цена")
    m1_min_price: orm.Mapped[float] = orm.mapped_column(Float, nullable=True)
    procedure_form: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Форма")
    auction_step: orm.Mapped[float] = orm.mapped_column(Float, nullable=True, comment="Шаг аукциона")
    price_decrease_step: orm.Mapped[float] = orm.mapped_column(Float, nullable=True, comment="Шаг понижения цены")

    applications_enddate: orm.Mapped[datetime] = orm.mapped_column(DateTime, nullable=True, comment="Дата окончания приема заявок")
    tendering: orm.Mapped[datetime] = orm.mapped_column(DateTime, nullable=True, comment="Проведение торгов")

    entrance_type: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Тип входа")
    windows: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Окна")
    ceilings: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Потолки")
    floor: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Этаж")

    lat: orm.Mapped[float] = orm.mapped_column(Float, nullable=True, comment="Широта")
    lon: orm.Mapped[float] = orm.mapped_column(Float, nullable=True, comment="Долгота")

    images_links: orm.Mapped[list[str]] = orm.mapped_column(ARRAY(String), nullable=True, comment="Ссылки на изображения (для авито)")


class ParkingSpacesTenders(Base):

    __tablename__ = "parking_spaces_tenders"

    tender_id: orm.Mapped[str] = orm.mapped_column(String, primary_key=True, comment="ID тендера")

    investmoscow_url: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Сылка на investmoscow")
    address: orm.Mapped[str] = orm.mapped_column(String, nullable=False, comment="Адрес")
    region_name: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Округ")
    district_name: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Район")
    subway_stations: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Метро")
    procedure_form: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Форма")
    start_price: orm.Mapped[float] = orm.mapped_column(Float, nullable=True, comment="Начальная цена")
    deposit: orm.Mapped[float] = orm.mapped_column(Float, nullable=True, comment="Задаток")
    applications_enddate: orm.Mapped[datetime] = orm.mapped_column(DateTime, nullable=True, comment="Дата окончания приема заявок")
    floor: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Этаж")
    parking_type: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Тип парковки")
    parking_place: orm.Mapped[str] = orm.mapped_column(String, nullable=True, comment="Место парковки")
    object_area: orm.Mapped[float] = orm.mapped_column(Float, nullable=True, comment="Площадь")
    count: orm.Mapped[int] = orm.mapped_column(Integer, nullable=True, comment="Количество")

    images_links: orm.Mapped[list[str]] = orm.mapped_column(ARRAY(String), nullable=True, comment="Ссылки на изображения (для авито)")

