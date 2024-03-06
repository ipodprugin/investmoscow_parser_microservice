import aiohttp
import asyncio
import json

from ..config import settings
from ..api.models import TenderImages, TenderImagesInfo
from ..database.handlers.images import db_add_images_links


def get_tenders_list():
    with open('photos.json', 'r', encoding='utf-8') as f:
        images = TenderImages.model_validate_json(f.read())
    return images.images


async def get_drive_info(session):
    url = 'https://cloud-api.yandex.net/v1/disk/'
    async with session.get(url) as response:
        return response.status, await response.json()


# async def get_item_info(session, fields: Optional[Union[str, bool]] = None, url: Optional[str] = None, path: Optional[str] = None):
async def get_item_info(
    session,
    url: str | None = None,
    path: str | None = None
):
    params = {}
    if not url:
        params['path'] = path
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
    async with session.get(url, params=params) as response:
        return response.status, await response.json()


async def publish_item(session, path: str):
    params = {'path': path}
    url = 'https://cloud-api.yandex.net/v1/disk/resources/publish'
    async with session.put(url, params=params) as response:
        return response.status, await response.json()


async def publish_items(session, path: str):
    status, response = await get_item_info(session=session, path=path)
    print(status, response)
    if status == 200:
        for image in response['_embedded']['items']:
            status, response = await publish_item(session=session, path=f'{path}/{image["name"]}')
            print(status, response)


async def create_folder(session, path):
    url = 'https://cloud-api.yandex.net/v1/disk/resources'
    params = {'path': path}
    async with session.put(url, params=params) as response:
        return response.status, await response.json()


async def upload_file_from_web(session, imageurl, path):
    url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    params = {
        'url': imageurl,
        'path': path
    }
    async with session.post(url, params=params) as response:
        return response.status, await response.json()


async def get_operation_status(session, url):
    async with session.get(url) as response:
        resp = await response.json()
        return resp['status']


async def upload_files(session, basepath, images):
    status_links = []
    upload_error = []
    for image in images['attached_images']:
        status, response = await upload_file_from_web(
            session,
            image['url'],
            f"{basepath}/{image['tender_id']}/{image['file_base']['name']}"
        )
        if status == 202:
            image['status_url'] = response['href']
            status_links.append(image)
            #     # 'url': image.url,
            #     # 'folder': path,
            #     # 'name': image.file_base.name,
            #     'image': image,
            #     'status_url': response['href'],
            # })
        else:
            upload_error.append(image)
        print('upload', response, status)
    return status_links, upload_error


async def check_images_upload_status(session, images_status_links):
    images_w_failed_status = []
    for images in images_status_links:
        for image in images['attached_images']: 
            async with session.get(image['status_url']) as response:
                resp = await response.json()
                if resp['status'] == 'failed':
                    images_w_failed_status.append(image)
                print('status:', resp['status'], image)
    return {'attached_images': images_w_failed_status}


async def upload_images(folder: str, tenders: list[TenderImagesInfo] | None = None):
    basepath = f'app:/{folder}'
    DISK_AUTH_HEADERS = {'accept': 'application/json', 'Authorization': 'OAuth %s' % settings.YADISK_OAUTH_TOKEN}

    if not tenders:
        tenders = get_tenders_list()
    images_status_links = []
    async with aiohttp.ClientSession(headers=DISK_AUTH_HEADERS) as session:
        status, response = await create_folder(session, basepath)
        if status != 201 and status != 409:
            print('Cant create folder:', response)
            return
        if status == 201:
            for tender in tenders:
                path = f'{basepath}/{tender.tender_id}'
                status, response = await create_folder(session, path=path)
                if status != 201:
                    print('Cant create folder:', response)
                    return
                status_links, upload_error = await upload_files(session, basepath, tender.model_dump())
                images_status_links.append({'attached_images': status_links})
        else:
            for tender in tenders:
                path = f'{basepath}/{tender.tender_id}'
                status, response = await get_item_info(session, path=path)
                if status == 404:
                    status, response = await create_folder(session, path=path)
                    if status != 201:
                        print('Cant create folder:', response)
                        return
                    status_links, upload_error = await upload_files(session, basepath, tender.model_dump())
                    images_status_links.append({'attached_images': status_links})
        print(images_status_links)
        
        for i in range(2):
            failed_images = await check_images_upload_status(session, images_status_links)
            if not failed_images:
                break
            with open(f'failed_{i}.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(failed_images, ensure_ascii=False, indent=4))
            status_links, upload_error = await upload_files(session, basepath, failed_images)
            images_status_links = [{'attached_images': status_links}]

            
    with open('disk.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(response, ensure_ascii=False, indent=4))


async def publish_images(session: aiohttp.ClientSession, basefolder: str, tenders_ids: list[str]):
    for tender_id in tenders_ids:
        foldername = f'{basefolder}/{tender_id[0]}'
        await publish_items(session=session, path='app:/' + foldername)


async def get_images_share_links(session: aiohttp.ClientSession, basefolder: str, tenders_ids: list[str]) -> dict[str, list[str]]:
    images_links = {}
    for tender_id in tenders_ids:
        foldername = f'{basefolder}/{tender_id[0]}'
        status, response = await get_item_info(session=session, path='app:/' + foldername)
        if status == 200:
            _images = []
            for image in response['_embedded']['items']:
                _images.append(image['public_url'])
            images_links[tender_id] = _images
    return images_links


async def process_images(basefolder: str, tenders_ids: list[str]):
    DISK_AUTH_HEADERS = {'accept': 'application/json', 'Authorization': 'OAuth %s' % settings.YADISK_OAUTH_TOKEN}
    async with aiohttp.ClientSession(headers=DISK_AUTH_HEADERS) as session:
        await publish_images(session, basefolder, tenders_ids)
        images_links = await get_images_share_links(session, basefolder, tenders_ids)
        await db_add_images_links(images_links)

