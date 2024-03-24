import re

from typing import Pattern

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # .env
    API_PORT: int
    API_HOST: str

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    DB_PORT: int

    SSL: bool = False

    YADISK_OAUTH_TOKEN: str

    PARKING_SPACES_FOLDERNAME: str = 'parking_spaces'
    NONRESIDENTIAL_FOLDERNAME: str = 'nonresidential'

    # defaults
    DB_URL: str

    GET_PARKPLACE_REGEX: Pattern = re.compile(r"(м/м №|м/м|мм)\s*(.+)")
    GET_PRICE_REGEX: Pattern = re.compile(r"\d[\d ]+,?\d+")
    GET_SQUARE_VALUE_REGEX: Pattern = re.compile(r"\d+,?\d*")

    DATETIME_WITH_SEC_FORMAT: str = '%d.%m.%Y %H:%M:%S'
    DATETIME_FORMAT: str = '%d.%m.%Y %H:%M'

    PAGENUMBER: int = 1
    PAGESIZE: int = 20

    SEARCH_FIELDS: list[str] = [
        'Тип входа',
        'Наличие окон и их размер',
        'Высота потолков, м',
        'Округ города Москвы',
        'Муниципальный район',
    ]

settings = Settings()

