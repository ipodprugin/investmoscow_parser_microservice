from pydantic import BaseModel, Field, ConfigDict, computed_field
from typing_extensions import Annotated
from typing import List
from enum import IntEnum
from datetime import datetime

from ..config import settings


class BaseConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class FileBase(BaseConfig):
    name: str


class AttachedImage(BaseConfig):
    tender_id: int = Field(..., alias='tenderId')
    is_main_photo: bool = Field(..., alias='isMainPhoto')
    url: str
    file_base: FileBase = Field(..., alias='fileBase')


class ImageInfo(BaseConfig):
    attached_images: Annotated[List[AttachedImage], Field(alias='attachedImages')]


class ObjectInfoItem(BaseConfig):
    label: str
    value: str


class ProcedureInfoItem(BaseConfig):
    label: str | None = None
    value: Annotated[str | None, Field(..., alias='value')] = None
    user_action: Annotated[str | None, Field(..., alias='userAction')] = None


class Coords(BaseConfig):
    lat: float = Field(..., alias='lat')
    lon: float = Field(..., alias='long')


class TenderDataFromFilesPayload(BaseConfig):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    entrance_type: Annotated[str | None, Field(..., alias='Тип входа')] = None
    windows: Annotated[str | None, Field(..., alias='Наличие окон и их размер')] = None
    ceilings: Annotated[str | None, Field(..., alias='Высота потолков, м')] = None
    region_name: Annotated[str | None, Field(..., alias='Округ города Москвы')] = None
    district_name: Annotated[str | None, Field(..., alias='Муниципальный район')] = None


class SubwayStation(BaseConfig):
    subwayStationId: Annotated[int | None , Field(..., alias='subwayStationId')] = None
    subwayStationName: Annotated[str | None , Field(..., alias='subwayStationName')] = None


class HeaderInfo2(BaseConfig):
    address: str
    subway: list[SubwayStation] | None = None
    land_area: Annotated[str, Field(alias='landArea')]


class MapInfo(BaseConfig):
    coords: Annotated[Coords | None, Field(..., alias='coords')] = None
    price: Annotated[float | None, Field(..., alias='price')] = None


class TenderBase(BaseConfig):
    tender_id: Annotated[int, Field(alias='tenderId')]
    image_info: Annotated[ImageInfo, Field(alias='imageInfo')]
    header_info: Annotated[HeaderInfo2, Field(alias='headerInfo')]
    map_info: Annotated[MapInfo, Field(alias='mapInfo')]
    procedure_info: Annotated[List[ProcedureInfoItem], Field(alias='procedureInfo')]
    object_info: Annotated[List[ObjectInfoItem], Field(alias='objectInfo')]

    @computed_field
    def investmoscow_url(self) -> str:
        return 'https://investmoscow.ru/tenders/tender/' + str(self.tender_id)

    @computed_field
    def deposit(self) -> float | None:
        deposit = list(filter(lambda x: x.label == 'Размер задатка', self.procedure_info))
        return extract_price(deposit[0].value) if deposit else None

    @computed_field
    def form(self) -> str | None:
        form = list(filter(lambda x: x.label == 'Форма проведения', self.procedure_info))
        return form[0].value if form else None

    @computed_field
    def floor(self) -> str | None:
        floor = list(filter(lambda x: x.label == 'Этаж', self.object_info))
        return floor[0].value if floor else None

    @computed_field
    def applications_enddate(self) -> datetime | None:
        applications_enddate = list(filter(lambda x: x.label == 'Дата окончания приёма заявок', self.procedure_info))
        return datetime.strptime(applications_enddate[0].value, settings.DATETIME_WITH_SEC_FORMAT) if applications_enddate else None

    @computed_field
    def start_price(self) -> float | None:
        return self.map_info.price if self.map_info.price else self.deposit * 2

    @computed_field
    def object_area(self) -> float | None:
        object_area = extract_square_value(self.header_info.land_area)
        return object_area if object_area else None


def extract_price(price):
    if not price:
        return 0
    price = price.replace('\xa0', '')
    price = settings.GET_PRICE_REGEX.findall(price)
    if price:
        return float(price[0].replace(" ", "").replace(",", "."))
    return 0


def extract_square_value(square_value):
    if not square_value:
        return 0
    square_value = square_value.replace('\xa0', '')
    square_value = settings.GET_SQUARE_VALUE_REGEX.findall(square_value)
    if square_value:
        return float(square_value[0].replace(" ", "").replace(",", "."))
    return 0


class ParkingSpacesDataValidate(TenderBase):

    @computed_field
    def parking_type(self) -> str | None:
        parking_type = list(filter(lambda x: x.label == 'Тип парковки', self.object_info))
        return parking_type[0].value if parking_type else None

    @computed_field
    def parking_place(self) -> str | None:
        parking_place = list(filter(lambda x: x.label == 'Расположение', self.object_info))
        parking_place = settings.GET_PARKPLACE_REGEX.findall(parking_place[0].value)
        return parking_place[0][-1] if parking_place else None


# TODO: Try to define dields, which is computed
class NonresidentialDataValidate(TenderBase, TenderDataFromFilesPayload):

    @computed_field
    def tendering(self) -> datetime | None:
        tendering = list(filter(lambda x: x.label == 'Проведение торгов', self.procedure_info))
        return datetime.strptime(tendering[0].value, settings.DATETIME_FORMAT) if tendering else None

    @computed_field
    def auction_step(self) -> float | None:
        auction_step = list(filter(lambda x: x.label == 'Шаг аукциона', self.procedure_info))
        return extract_price(auction_step[0].value) if auction_step else None

    @computed_field
    def price_decrease_step(self) -> float | None:
        price_decrease_step = list(filter(lambda x: x.label == 'Шаг понижения цены', self.procedure_info))
        return extract_price(price_decrease_step[0].value) if price_decrease_step else None

    @computed_field
    def min_price(self) -> float | None:
        min_price = list(filter(lambda x: x.label == 'Цена отсечения', self.procedure_info))
        return extract_price(min_price[0].value) if min_price else None

    @computed_field
    def m1_start_price(self) -> float | None:
        m1_start_price = self.deposit * 2 / self.object_area if self.object_area else None
        return m1_start_price

    @computed_field
    def m1_min_price(self) -> float | None:
        if self.object_area and self.min_price:
            return self.min_price / self.object_area


class NonresidentialDataDB(BaseConfig):
    tender_id: Annotated[str, Field(description='tender_id')]
    investmoscow_url: Annotated[str | None, Field(..., description='Сылка на investmoscow')] = None
    address: Annotated[str | None, Field(..., description='Адрес')] = None 
    region_name: Annotated[str | None, Field(..., description='Округ')] = None 
    district_name: Annotated[str | None, Field(..., description='Район')] = None 
    subway_stations: Annotated[str | None, Field(..., description='Метро')] = None 
    object_area: Annotated[float | None, Field(..., description='Площадь')] = None
    floor: Annotated[str | None, Field(..., description='Этаж')] = None
    applications_enddate: Annotated[datetime | None, Field(..., description='Дата окончания приема заявок')] = None
    deposit: Annotated[float | None, Field(..., description='Задаток')] = None
    start_price: Annotated[float | None, Field(..., description='Начальная цена')] = None 
    m1_start_price: Annotated[float | None, Field(..., description='')] = None
    min_price: Annotated[float | None, Field(..., description='Минимальная цена')] = None
    m1_min_price: Annotated[float | None, Field(..., description='')] = None
    procedure_form: Annotated[str | None, Field(..., description='Форма')] = None
    auction_step: Annotated[float | None, Field(..., description='Шаг аукциона')] = None
    price_decrease_step: Annotated[float | None, Field(..., description='Шаг понижения цены')] = None
    tendering: Annotated[datetime | None, Field(..., description='Проведение торгов')] = None
    lat: Annotated[float | None, Field(..., description='Широта')] = None
    lon: Annotated[float | None, Field(..., description='Долгота')] = None
    entrance_type: Annotated[str | None, Field(..., description='Тип входа')] = None
    windows: Annotated[str | None, Field(..., description='Окна')] = None
    ceilings: Annotated[str | None, Field(..., description='Потолки')] = None
    images_links: Annotated[list[str] | None, Field(..., description='Ссылки на изображения (для авито)')] = None


class NonresidentialDataOut(NonresidentialDataDB):

    @computed_field
    def imgzippath(self) -> str:
        return f'app:/{settings.NONRESIDENTIAL_FOLDERNAME}/{self.tender_id}'


class ParkingSpacesDataOut(BaseConfig):
    tender_id: str
    investmoscow_url: str | None = None
    address: str | None = None 
    subway_stations: str | None = None 
    region_name: str | None = None 
    district_name: str | None = None 
    object_area: float | None = None
    floor: str | None = None
    applications_enddate: datetime | None = None
    deposit: float | None = None
    start_price: float | None = None 
    procedure_form: str | None = None
    parking_type: str | None = None
    parking_place: str | None = None
    count: int | None = None
    images_links: list[str] | None = None


class TenderTypes(IntEnum):
    parking_space = 30011578
    nonresidential = 30011569


class AttachedImageSnakeCase(BaseConfig):
    tender_id: Annotated[int, Field(alias='tender_id')]
    is_main_photo: Annotated[bool, Field(alias='is_main_photo')]
    url: str
    file_base: Annotated[FileBase, Field(alias='file_base')]


class TenderImagesInfo(BaseConfig):
    tender_id: Annotated[int, Field(alias='tender_id')]
    attached_images: Annotated[list[AttachedImageSnakeCase], Field(alias='attached_images')]


class TenderImages(BaseConfig):
    images: list[TenderImagesInfo]

