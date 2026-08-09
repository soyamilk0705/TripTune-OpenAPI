from api.api_handler import fetch_total_api_items
from utils.log_handler import setup_logger
from db.db_handler import DatabaseHandler
from aws.s3_handler import S3Handler
from db import area_db, travel_image_db, travel_place_db

logger = setup_logger()


def korea_city_code(db : DatabaseHandler, secret_key : str, base_url : str):
    """
    도시 데이터를 조회 및 저장한다.

    [Parameter]
    db: mysql 데이터베이스 연결
    secret_key: open api 연동을 위해 사용할 키
    base_url: open api url 정보
    """
    url = base_url + '/ldongCode2'

    params = {
        'serviceKey': secret_key,
        'numOfRows': 10,
        'pageNo': 1,
        'MobileOS': 'ETC',
        'MobileApp': 'TripTune',
        '_type': 'json',
    }

    # DB 에 저장된 나라 id 조회
    country_id = area_db.get_country_id(db, '대한민국')['country_id']
    items = fetch_total_api_items(url, params)

    for item in items:
        api_city_code = item['code']
        city_name = item['name']

        area_db.insert_city(db, country_id, api_city_code, city_name)

    db.commit()

    logger.info("city 데이터 저장 완료")



def korea_district_code(db : DatabaseHandler, secret_key : str, base_url : str):
    """
    시군구 데이터를 조회 및 저장한다.
    api 요청 시 parameter 중 areaCode 에 open api 에서 지정한 도시의 id 값을 넣어 요청한다.

    [Parameter]
    db: mysql 데이터베이스 연결
    secret_key: open api 연동을 위해 사용할 키
    base_url: open api url 정보
    """
    url = base_url + '/ldongCode2'

    params = {
        'serviceKey': secret_key,
        'numOfRows': 10,
        'pageNo': 1,
        'MobileOS': 'ETC',
        'MobileApp': 'TripTune',
        '_type': 'json',
    }

    # DB 에 저장된 city 데이터 조회
    cities = area_db.get_cities(db)

    for city in cities:
        city_id = city['city_id']
        params['lDongRegnCd'] = city['api_city_code']

        items = fetch_total_api_items(url, params)

        for item in items:
            api_district_code = item['code']
            district_name = item['name']

            area_db.insert_district(db, city_id, api_district_code, district_name)

    db.commit()

    logger.info("district 데이터 저장 완료")


    
def delete_district_data(db : DatabaseHandler, s3 : S3Handler, district_id : int):
    """
    시군구 데이터를 삭제한다. 삭제 시 해당 시군구에 포함된 여행지, 여행지 이미지도 함께 삭제한다.
    
    - district 데이터 삭제
    - travel_place 데이터 삭제
    - travel_image 데이터 삭제
    - S3 이미지 삭제
    """
    try:
        travel_image_db.delete_travel_image_by_district(db, district_id)
        travel_place_db.delete_travel_place_by_district(db, district_id)
        area_db.delete_district(db, district_id)

        db.commit()

        s3.delete_objects_by_district(district_id)

        logger.info(f"district_id {district_id}번 데이터 삭제 완료")

    except Exception:
        db.rollback()
        logger.exception(f"district_id {district_id}번 데이터 삭제 실패")
        raise