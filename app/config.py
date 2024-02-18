import re

from typing import Pattern

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_PORT: int

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    DB_URL: str
    DB_PORT: int

    REDIS_HOST: str
    REDIS_PORT: int

    # # in .env file
    # PAGENUMBER: int
    # PAGESIZE: int
    # GSHEETS_CREDS_PATH: str = 'service_account_secret.json'
    # GSHEETURL: str = 'https://docs.google.com/spreadsheets/d/13uQGQqIcttvEyjCzpD1bJl1fPFQRNacjepl0y0iDyTQ/edit?usp=sharing'
    # PARKING_PLACES_WORKSHEET_NAME: str
    # NONRESIDENTIAL_SPACES_WORKSHEET_NAME: str
    # YADISK_OAUTH_TOKEN: str
    #
    # # defaults
    # PARK_OBJTYPE_ID: int = 30011578
    # NONRESIDENTIAL_OBJTYPE_ID: int = 30011569
    # BASEURL: str = 'https://investmoscow.ru'
    # DATETIME_FORMAT: str = '%Y-%m-%dT%H:%M:%S.%f0000Z'
    # PARKING_SHEET_COLUMNS: list = [
    #     '№', 
    #     'tender_id', 
    #     'Адрес', 
    #     'Округ', 
    #     'Район', 
    #     'Форма', 
    #     'Начальная цена', 
    #     'Задаток', 
    #     'Проведены', 
    #     'Дата окончания приема заявок', 
    #     'Колличество', 
    #     'Этаж', 
    #     'Тип парковки', 
    #     'Ссылка на investmoscow', 
    #     'ссылка на авито', 
    #     'ссылка на циан', 
    #     'Рыночная цена', 
    #     'Цена на прошедших торгах', 
    #     'Ставка на торгах', 
    #     'Выставлены на авито', 
    #     'Примечание', 
    #     'Интересный', 
    #     'Место', 
    #     'Площадь'
    # ]
    # NONRESIDENTIAL_SHEET_COLUMNS: list = [
    #     '№', 
    #     'tender_id', 
    #     'Адрес', 
    #     'Округ', 
    #     'Район', 
    #     'Форма', 
    #     'Начальная цена', 
    #     'Задаток', 
    #     'Этаж', 
    #     'Проведены', 
    #     'Дата окончания приема заявок', 
    #     'Ссылка на investmoscow', 
    #     'Ставка на торгах', 
    #     'Выставленны на авито', 
    #     'Примечание', 
    #     'Цена за кв м', 
    #     'Рыночная', 
    #     'Площадь',
    #     'Вход',
    #     'Шаг аукциона',
    #     'Шаг понижения цены',
    #     'Минимальная цена',
    #     'Проведение торгов',
    #     'Широта',
    #     'Долгота',
    # ]
    GET_PARKPLACE_REGEX: Pattern = re.compile(r"(м/м №|м/м|мм)\s*(.+)")
    GET_PRICE_REGEX: Pattern = re.compile(r"\d[\d ]+,?\d+")
    GET_SQUARE_VALUE_REGEX: Pattern = re.compile(r"\d+,?\d*")
    DATETIME_WITH_SEC_FORMAT: str = '%d.%m.%Y %H:%M:%S'
    DATETIME_FORMAT: str = '%d.%m.%Y %H:%M'
    PAGENUMBER: int | None = 1
    PAGESIZE: int | None = 20

settings = Settings()

