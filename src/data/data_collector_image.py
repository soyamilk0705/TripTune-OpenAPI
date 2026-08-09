import uuid
from datetime import datetime
from api.api_handler import logger, fetch_first_page_api_items
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
    commit/rollback은 호출한 곳에서 관리한다.
    """
    # s3에 업로드한 이미지들의 s3_object_key
    uploaded_keys = []

    # 상세 이미지 api 요청
    items = get_travel_detail_images(place.api_content_id)

    # ----------------------------
    # 신규 이미지 저장
    # ----------------------------
    for item in items:
        key = save_travel_image(
            db,
            s3,
            place,
            item['originimgurl'],
            False,
            item['serialnum']
        )
        uploaded_keys.append(key)

    logger.info(f"[END] {place.place_name}({place.api_content_id}) {len(items)}개 상세 이미지 신규 저장 완료")
    return uploaded_keys


def sync_travel_detail_images(db : DatabaseHandler, s3 : S3Handler, place : TravelPlace):
    """
    신규 상세 이미지를 저장한 후 기존 이미지를 삭제한다.
    commit/rollback은 호출한 곳에서 관리한다.
    """

    items = get_travel_detail_images(place.api_content_id)
    saved_detail_images = travel_image_db.get_travel_detail_images(db, place.place_id)

    uploaded_keys = []

    # ----------------------------
    # 신규 이미지 저장
    # ----------------------------
    for item in items:
        key = save_travel_image(
            db,
            s3,
            place,
            item['originimgurl'],
            False,
            item['serialnum']
        )
        uploaded_keys.append(key)

    # ----------------------------
    # 기존 이미지 삭제
    # ----------------------------
    if not saved_detail_images:
        logger.info(f"[SKIP] {place.place_name}({place.api_content_id}) 기존 상세 이미지 없음")
    else:
        for image in saved_detail_images:
            travel_image_db.delete_travel_detail_images(db, image['travel_image_id'])
            s3.delete_object(image['s3_object_key'])

    logger.info(f"[END] {place.place_name}({place.api_content_id}) {len(items)}개 상세 이미지 갱신 완료")

    return uploaded_keys




def get_travel_detail_images(api_content_id : int):
    """
    파라미터로 전달된 지역을 이용해 관광지 데이터를 DB에서 조회한다.
    DB에서 조회한 관광지 데이터를 이용해 open api에 이미지를 조회 후 데이터를 정제해 반환한다.

    """
    url = BASE_URL + '/detailImage2'

    params = build_image_params()
    params['contentId'] = api_content_id

    return fetch_first_page_api_items(url, params)
    

def sync_thumbnail_travel_image(db : DatabaseHandler, 
                                s3 : S3Handler, 
                                place : TravelPlace, 
                                image_url : str):
    """
    여행지의 썸네일 이미지를 신규 저장한 후 기존 이미지를 삭제한다.
    """
    thumbnail_image = travel_image_db.get_travel_thumbnail_image(db, place.place_id)

    # ----------------------------
    # 저장된 썸네일 없으면 신규 저장
    # ----------------------------
    if thumbnail_image is None:
        return save_travel_image(
            db,
            s3,
            place,
            image_url,
            True,
            None
        )

    # 동일한 이미지면 아무것도 하지 않음
    if thumbnail_image['api_file_url'] == image_url:
        logger.info(f"[SKIP] {place.place_name}({place.api_content_id}) 썸네일 변경 없음")
        return None

    # ----------------------------
    # 신규 썸네일 저장
    # ----------------------------
    new_key = save_travel_image(
        db,
        s3,
        place,
        image_url,
        True,
        None
    )

    # ----------------------------
    # 기존 썸네일 삭제
    # ----------------------------
    travel_image_db.delete_travel_thumbnail_image(db, thumbnail_image['travel_image_id'])
    s3.delete_object(thumbnail_image['s3_object_key'])

    logger.info(f"[END] {place.place_name}({place.api_content_id}) 썸네일 갱신 완료")

    return new_key


def save_travel_image(db : DatabaseHandler, 
                      s3 : S3Handler, 
                      place : TravelPlace, 
                      image_url : str, 
                      is_thumbnail : bool, 
                      serial_number : str | None):
    """
    파라미터로 전달된 관광지 이미지 데이터를 DB, S3에 저장한다.
    이미지 파일의 경우 S3에 이미지 파일로 저장된다.

    *is_thumbnail이 True/False 에 따라서 저장되는 이미지 파일명이 다르게 설정했다.

    """

    if is_thumbnail:
        file_name = f"{datetime.now():%y%m%d%H%M%S}_{place.place_id}_firstimage_{uuid.uuid4().hex[:8]}.jpg"
    else:
        file_name = f"{datetime.now():%y%m%d%H%M%S}_{place.place_id}_secondimage_{uuid.uuid4().hex[:8]}.jpg"
    
    original_name = image_url.split('/')[-1]
    s3_object_key = 'img/korea/' + str(place.location.district_id).zfill(2) + '/' + file_name


    # 이미지 다운 및 압축
    compressed_image, file_size = download_and_compress_image(image_url, 70)
    
    # s3 이미지 저장
    s3.upload_file(compressed_image, s3_object_key)

    # db 이미지 데이터 저장
    now = datetime.now()

    assert place.place_id is not None
    travel_image = TravelImage(
        place_id=place.place_id,
        s3_object_key=s3_object_key,
        original_name=original_name,
        file_name=file_name,
        file_type='jpg',
        file_size=file_size,
        created_at=now,
        updated_at=now,
        is_thumbnail=is_thumbnail,
        api_file_url=image_url,
        serial_number=serial_number
    )

    travel_image_db.insert_travel_image(db, travel_image)
    return s3_object_key


def extract_s3_key(url: str) -> str:
    """
    s3 객체 url 에서 key 추출 함수

    """
    parsed = urlparse(url)
    return parsed.path.lstrip('/')