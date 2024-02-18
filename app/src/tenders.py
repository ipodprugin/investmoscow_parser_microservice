import aiohttp
import json

from ..api.models import Tender


async def get_tenders(session: aiohttp.ClientSession, page_number, page_size, objtype_id):
    payload = """
    {
        "pageNumber": %d,
        "pageSize": %d,
        "orderBy": "Relevance",
        "orderAsc": false,
        "objectTypes": ["nsi:41:%d"],
        "tenderStatus": "nsi:tender_status_tender_filter:1",
        "timeToPublicTransportStop": {
            "noMatter": true
        }
    }
    """

    headers = {
        'authority': "api.investmoscow.ru",
        'accept': "application/json",
        'accept-language': "ru-RU",
        'content-type': "application/json",
        'origin': "https://investmoscow.ru",
        'referer': "https://investmoscow.ru/",
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "YaBrowser";v="23"',
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': "empty",
        'sec-fetch-mode': "cors",
        'sec-fetch-site': "same-site",
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.2271 YaBrowser/23.9.0.2271 Yowser/2.5 Safari/537.36",
        'x-requested-with': "XMLHttpRequest"
    }

    url = 'https://api.investmoscow.ru/investmoscow/tender/v2/filtered-tenders/searchTenderObjects'

    async with session.post(url, headers=headers, data=payload % (page_number, page_size, objtype_id)) as response:
        data = await response.json()

    with open(f'/src/jsons/objects.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return data


async def get_tender(session: aiohttp.ClientSession, tender_id: str):
    headers = {
        'authority': "api.investmoscow.ru",
        'accept': "application/json",
        'accept-language': "ru-RU",
        'origin': "https://investmoscow.ru",
        'referer': "https://investmoscow.ru/",
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "YaBrowser";v="23"',
        'sec-ch-ua-mobile': "?0",
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': "empty",
        'sec-fetch-mode': "cors",
        'sec-fetch-site': "same-site",
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.2271 YaBrowser/23.9.0.2271 Yowser/2.5 Safari/537.36",
        'x-requested-with': "XMLHttpRequest"
    }
    url = "https://api.investmoscow.ru/investmoscow/tender/v1/object-info/getTenderObjectInformation?tenderId=" + tender_id

    async with session.get(url, headers=headers) as response:
        data = await response.json()

    with open(f'/src/jsons/{tender_id}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return data


async def get_tender2(tender_id: int):
    with open(f'/src/jsons/{tender_id}.json', 'r', encoding='utf-8') as f:
        tender = json.load(f)
    return tender


def get_tender_docs_files(documents):
    for doc in documents:
        if doc.get('groupType') == 'ObjectDocs':
            return doc.get('files')


def get_tender_doc_url_by_name(files_info, search_doc_name):
    for file in files_info:
        filename = file.get('name')
        if filename and filename.startswith(search_doc_name):
            return file.get('downloadLink')


async def get_evaluation_report_link(tender_data: dict):
    try:
        tender_type = tender_data['headerInfo']['tenderTypeName']
        if tender_type == 'Аренда':
            return None
        documents = tender_data['documentInfo']['documentGroups']
    except KeyError:
        print("can't get documentInfo or documentGroups")
        return None

    tender_docs_files = get_tender_docs_files(documents)
    if not tender_docs_files:
        return None

    evaluation_report_doclink = get_tender_doc_url_by_name(tender_docs_files, 'Отчет об оценке')
    if not evaluation_report_doclink:
        return None

    return evaluation_report_doclink

