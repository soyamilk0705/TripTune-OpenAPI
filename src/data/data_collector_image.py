import os
import uuid
import datetime
from api.api_handler import *
from utils.utils import *
from utils.config import *
from utils.log_handler import setup_logger
from db.db_handler import DatabaseHandler
from aws import S3Handler
from model import *
from urllib.parse import urlparse


def korea_travel_detail_image(db, s3):
    '''
    DB에서 조회한 관광지 데이터를 이용해 open api에 이미지를 조회 및 저장한다.
    이미지 파일의 경우 S3에 이미지 파일로 저장된다.
    저장 위치: travel_image
    
    '''
    url = BASE_URL + '/detailImage1'

    params = build_image_params()

    select_place = "SELECT * FROM travel_place"
    travel_places = db.execute_select_all(select_place)

    if not travel_places:
        logger.error(f'여행지 정보가 존재하지 않습니다')
        return

    for place in travel_places:
        params['contentId'] = place['api_content_id']

        total_count = get_total_count(url, params)
        items = []

        if total_count != 0:
            items = fetch_items(url, params, total_count)

            for item in items:
                image_url = item['originimgurl']
                save_travel_image(db, s3, place['district_id'], place['place_id'], image_url, False)

        logger.info(f'{place["place_name"]} {total_count}개 이미지 데이터 저장 완료')
    logger.info('korea_travel_detail_image() - 이미지 데이터 저장 완료')




def limited_korea_travel_detail_image(db, s3, api_content_id):
    '''
    파라미터로 전달된 지역을 이용해 관광지 데이터를 DB에서 조회한다.
    DB에서 조회한 관광지 데이터를 이용해 open api에 이미지를 조회 및 저장한다.
    이미지 파일의 경우 S3에 이미지 파일로 저장된다.
    저장 위치: travel_image

    '''
    url = BASE_URL + '/detailImage1'

    params = build_image_params()
    params['contentId'] = api_content_id

    # 여행지 데이터 조회
    place = db.execute_select_one("SELECT * FROM travel_place WHERE api_content_id = %s", api_content_id)

    if not place:
        logger.error(f'여행지 정보가 존재하지 않습니다 - {api_content_id}')
        return

    total_count = get_total_count(url, params)
    items = []

    if total_count != 0:
        items = fetch_one_page_items(url, params)

        for item in items:
            image_url = item['originimgurl']
            save_travel_image(db, s3, place['district_id'], place['place_id'], image_url, False)

        logger.info(f'{place["place_name"]} {len(items)}개 이미지 데이터 저장 완료')
    logger.info('limited_korea_travel_detail_image() - 이미지 데이터 저장 완료')



def save_travel_image(db, s3, district_id, place_id, image_url, is_thumbnail):
    '''
    파라미터로 전달된 관광지 이미지 데이터를 DB, S3에 저장한다.
    이미지 파일의 경우 S3에 이미지 파일로 저장된다.

    *is_thumbnail이 True/False 에 따라서 저장되는 이미지 파일명이 다르게 설정했다.

    '''
    if image_url is not None:
        if is_thumbnail:
            file_name = datetime.now().strftime('%y%m%d%H%M%S') + '_' + str(place_id) + '_firstimage_' + uuid.uuid4().hex[:8] + '.jpg'
        else:
            file_name = datetime.now().strftime('%y%m%d%H%M%S') + '_' + str(place_id) + '_secondimage_' + uuid.uuid4().hex[:8] + '.jpg'

        
        original_name = image_url.split('/')[-1]
        object_key = 'img/korea/' + str(district_id).zfill(2) + '/' + file_name


        # 이미지 다운 및 압축
        compressed_image, file_size = download_and_compress_image(image_url, 70)
        
        # s3 이미지 저장
        s3.upload_file(compressed_image, object_key)

        # db 이미지 데이터 저장
        travel_image = TravelImage(
            place_id,
            object_key,
            original_name,
            file_name,
            'jpg',
            file_size,
            datetime.now(),
            datetime.now(),
            is_thumbnail,
            image_url
        )

        db.insert_travel_image(travel_image)
       
        logger.info(f'save_travel_image() - db, s3 이미지 데이터 저장 완료(썸네일 여부 : {is_thumbnail})')


def extract_s3_key(url: str) -> str:
    '''
    s3 객체 url 에서 key 추출 함수

    '''
    parsed = urlparse(url)
    return parsed.path.lstrip('/')