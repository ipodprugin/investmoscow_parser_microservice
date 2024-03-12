from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from typing_extensions import Annotated

from typing import List, Optional

from enum import IntEnum

from ..config import settings

from datetime import datetime


class FileBase(BaseModel):
    name: str


class HeaderInfo(BaseModel):
    address: str


class AttachedImage(BaseModel):
    tender_id: int = Field(..., alias='tenderId')
    is_main_photo: bool = Field(..., alias='isMainPhoto')
    url: str
    file_base: FileBase = Field(..., alias='fileBase')


class ImageInfo(BaseModel):
    attached_images: Annotated[List[AttachedImage], Field(alias='attachedImages')]


class ObjectInfoItem(BaseModel):
    label: str
    value: str


class ProcedureInfoItem(BaseModel):
    label: str | None = None
    value: Annotated[str | None, Field(..., alias='value')] = None
    user_action: Annotated[str | None, Field(..., alias='userAction')] = None


class Coords(BaseModel):
    lat: float = Field(..., alias='lat')
    lon: float = Field(..., alias='long')


class MapInfoItem(BaseModel):
    coords: Optional[Coords] = Field(None, alias='coords')


class BaseTender(BaseModel):
    tender_id: int = Field(..., alias='tenderId')
    url: Optional[str] = None
    region_name: Optional[str] = Field(None, alias='regionName')
    district_name: Optional[str] = Field(None, alias='districtName')
    object_area: Optional[float] = Field(None, alias='objectArea')
    start_price: Optional[float] = Field(None, alias='startPrice')
    request_end_date: Optional[str] = Field(None, alias='requestEndDate')


class Tender(BaseTender):
    image_info: Optional[ImageInfo] = Field(None, alias='imageInfo')
    header_info: Optional[HeaderInfo] = Field(None, alias='headerInfo')
    object_info: Optional[List[ObjectInfoItem]] = Field(None, alias='objectInfo')
    procedure_info: Optional[List[ProcedureInfoItem]] = Field(
        None, alias='procedureInfo'
    )
    map_info: Optional[MapInfoItem] = Field(None, alias='mapInfo')


class TenderDataFromFilesPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    entrance_type: Annotated[str | None, Field(..., alias='Тип входа')] = None
    windows: Annotated[str | None, Field(..., alias='Наличие окон и их размер')] = None
    ceilings: Annotated[str | None, Field(..., alias='Высота потолков, м')] = None
    region_name: Annotated[str | None, Field(..., alias='Округ города Москвы')] = None
    district_name: Annotated[str | None, Field(..., alias='Муниципальный район')] = None


class TenderOut(TenderDataFromFilesPayload):
    tender_id: str = Field(alias='tender_id')


# -----------------------------------------------------------------------------------------



class SubwayStation(BaseModel):
    subwayStationId: Annotated[int | None , Field(..., alias='subwayStationId')] = None
    subwayStationName: Annotated[str | None , Field(..., alias='subwayStationName')] = None


class HeaderInfo2(BaseModel):
    address: str
    subway: list[SubwayStation] | None = None
    land_area: Annotated[str, Field(alias='landArea')]


class MapInfo(BaseModel):
    coords: Annotated[Coords | None, Field(..., alias='coords')] = None
    price: Annotated[float | None, Field(..., alias='price')] = None


class TenderBase(BaseModel):
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


class NonresidentialDataOut(BaseModel):
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
    m1_start_price: float | None = None
    min_price: float | None = None
    m1_min_price: float | None = None
    procedure_form: str | None = None
    auction_step: float | None = None
    price_decrease_step: float | None = None
    tendering: datetime | None = None
    lat: float | None = None
    lon: float | None = None
    entrance_type: str | None = None
    windows: str | None = None
    ceilings: str | None = None


class ParkingSpacesDataOut(BaseModel):
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


class TenderTypes(IntEnum):
    parking_space = 30011578
    nonresidential = 30011569


# Images

class AttachedImageSnakeCase(BaseModel):
    tender_id: Annotated[int, Field(alias='tender_id')]
    is_main_photo: Annotated[bool, Field(alias='is_main_photo')]
    url: str
    file_base: Annotated[FileBase, Field(alias='file_base')]


class TenderImagesInfo(BaseModel):
    tender_id: Annotated[int, Field(alias='tender_id')]
    attached_images: Annotated[list[AttachedImageSnakeCase], Field(alias='attached_images')]


class TenderImages(BaseModel):
    images: list[TenderImagesInfo]

