import uuid
from datetime import datetime
from api.api_handler import logger, fetch_one_page_api_items
from utils.utils import download_and_compress_image
from utils.config import BASE_URL, build_image_params
from db.db_handler import DatabaseHandler
from db import travel_image_db
from aws.s3_handler import S3Handler
from model.travel_place import TravelPlace
from model.travel_image import TravelImage
from urllib.parse import urlparse



def save_travel_detail_images(db : DatabaseHandler, s3 : S3Handler, place : TravelPlace):
    """
    여행지의 상세 이미지를 저장한다.
    """
    # 상세 이미지 요청
    items = get_travel_detail_images(place.api_content_id)

    for item in items:
        image_url = item['originimgurl']
        serial_number = item['serialnum']
        save_travel_image(db, s3, place, image_url, False, serial_number)

    logger.info(f'[save_travel_detail_images()] {place.place_name} {len(items)}개 이미지 데이터 저장 완료')


def sync_travel_detail_images(db : DatabaseHandler, s3 : S3Handler, place : TravelPlace):
    """
    기존에 있던 여행지의 상세 이미지를 삭제 후 신규 저장한다. 
    """
    # 상세 이미지 요청
    items = get_travel_detail_images(place.api_content_id)

    # 기존 이미지 삭제
    detail_images = travel_image_db.get_travel_detail_images(db, place.place_id)

    for image in detail_images:
            s3.delete_object(image['s3_object_key'])

    travel_image_db.delete_travel_detail_images(db, place.place_id)


    for item in items:
        image_url = item['originimgurl']
        serial_number = item['serialnum']
        save_travel_image(db, s3, place, image_url, False, serial_number)

    logger.info(f'[sync_travel_detail_images()] {place.place_name} {len(items)}개 이미지 데이터 삭제 후 저장 완료')


def get_travel_detail_images(api_content_id : int):
    '''
    파라미터로 전달된 지역을 이용해 관광지 데이터를 DB에서 조회한다.
    DB에서 조회한 관광지 데이터를 이용해 open api에 이미지를 조회 후 데이터를 정제해 반환한다.

    '''
    url = BASE_URL + '/detailImage2'

    params = build_image_params()
    params['contentId'] = api_content_id

    return fetch_one_page_api_items(url, params)
    

def sync_thumbnail_travel_image(db : DatabaseHandler, 
                                s3 : S3Handler, 
                                place : TravelPlace, 
                                image_url : str):
    """
    여행지의 썸네일 이미지를 삭제 후 신규 저장한다.
    """
    thumbnail_image = travel_image_db.get_travel_thumbnail_image(db, place.place_id)

    if thumbnail_image and thumbnail_image['api_file_url'] != image_url:
        s3.delete_object(thumbnail_image['s3_object_key'])
        travel_image_db.delete_travel_thumbnail_image(db, place.place_id)
        save_travel_image(db, s3, place, image_url, True, None)
        logger.info(f'[sync_thumbnail_travel_image()] {place.place_name} 썸네일 삭제 후 저장 완료')



def save_travel_image(db : DatabaseHandler, 
                      s3 : S3Handler, 
                      place : TravelPlace, 
                      image_url : str, 
                      is_thumbnail : bool, 
                      serial_number : str | None):
    '''
    파라미터로 전달된 관광지 이미지 데이터를 DB, S3에 저장한다.
    이미지 파일의 경우 S3에 이미지 파일로 저장된다.

    *is_thumbnail이 True/False 에 따라서 저장되는 이미지 파일명이 다르게 설정했다.

    '''

    if is_thumbnail:
        file_name = f"{datetime.now():%y%m%d%H%M%S}_{place.place_id}_firstimage_{uuid.uuid4().hex[:8]}.jpg"
    else:
        file_name = f"{datetime.now():%y%m%d%H%M%S}_{place.place_id}_secondimage_{uuid.uuid4().hex[:8]}.jpg"
    
    original_name = image_url.split('/')[-1]
    s3_object_key = 'img/korea/' + str(place.district_id).zfill(2) + '/' + file_name


    # 이미지 다운 및 압축
    compressed_image, file_size = download_and_compress_image(image_url, 70)
    
    # s3 이미지 저장
    s3.upload_file(compressed_image, s3_object_key)

    # db 이미지 데이터 저장
    now = datetime.now()
    travel_image = TravelImage(
        place.place_id,
        s3_object_key,
        original_name,
        file_name,
        'jpg',
        file_size,
        now,
        now,
        is_thumbnail,
        image_url,
        serial_number
    )

    travel_image_db.insert_travel_image(db, travel_image)
    
    logger.info(f'[save_travel_image()] db, s3 이미지 데이터 저장 완료(썸네일 여부 : {is_thumbnail})')


def extract_s3_key(url: str) -> str:
    '''
    s3 객체 url 에서 key 추출 함수

    '''
    parsed = urlparse(url)
    return parsed.path.lstrip('/')