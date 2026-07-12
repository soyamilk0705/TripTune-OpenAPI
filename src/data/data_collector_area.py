from api.api_handler import *
from utils.utils import *
from utils.log_handler import setup_logger
from db.db_handler import DatabaseHandler
from aws import S3Handler

logger = setup_logger()


def korea_city_code(db : DatabaseHandler, secret_key : str, base_url : str):
    '''
    도시 데이터를 조회 및 저장한다.


    [Parameter]
    db: mysql 데이터베이스 연결
    secret_key: open api 연동을 위해 사용할 키
    base_url: open api url 정보
    '''
    url = base_url + '/areaCode1'

    params = {
        'serviceKey': secret_key,
        'numOfRows': 10,
        'pageNo': 1,
        'MobileOS': 'ETC',
        'MobileApp': 'TripTune',
        '_type': 'json',
    }

    # 전체 갯수 조회
    total_count = get_total_count(url, params)

    # DB 에 저장된 나라 id 조회
    select_country = 'SELECT country_id FROM country WHERE country_name = "대한민국"'
    country_id = db.fetch_one(select_country)['country_id']

    items = fetch_items(url, params, total_count)

    for item in items:
        area_code = item['code']
        city_name = item['name']

        insert_city = 'INSERT INTO city(country_id, api_area_code, city_name) VALUES (%s, %s, %s)'
        db.execute_insert(insert_city, (country_id, area_code, city_name))

    logger.info('city 데이터 저장 완료')



def korea_district_code(db : DatabaseHandler, secret_key : str, base_url : str):
    '''
    시군구 데이터를 조회 및 저장한다.
    api 요청 시 parameter 중 areaCode 에 open api 에서 지정한 도시의 id 값을 넣어 요청한다.


    [Parameter]
    db: mysql 데이터베이스 연결
    secret_key: open api 연동을 위해 사용할 키
    base_url: open api url 정보
    '''
    url = base_url + '/areaCode1'

    params = {
        'serviceKey': secret_key,
        'numOfRows': 10,
        'pageNo': 1,
        'MobileOS': 'ETC',
        'MobileApp': 'TripTune',
        '_type': 'json',
    }

    # DB 에 저장된 city 데이터 조회
    select_city = 'SELECT city_id, api_area_code FROM city'
    cities = db.execute_select_all(select_city)
    

    for city in cities:
        city_id = city['city_id']
        params['areaCode'] = city['api_area_code']
        
        # 전체 갯수 조회
        total_count = get_total_count(url, params)
        items = fetch_items(url, params, total_count)

        for item in items:
            sigungu_code = item['code']
            district_name = item['name']

            insert_district = 'INSERT INTO district(city_id, api_sigungu_code, district_name) VALUES (%s, %s, %s)'
            db.execute_insert(insert_district, (city_id, sigungu_code, district_name))
        
    logger.info('district 데이터 저장 완료')


    
def delete_district_data(db : DatabaseHandler, s3 : S3Handler, district_id : int):
    """
    시군구 데이터를 삭제한다. 삭제 시 해당 시군구에 포함된 여행지, 여행지 이미지도 함께 삭제한다.
    
    - distrct 데이터 삭제
    - travel_place 데이터 삭제
    - travel_image 데이터 삭제
    - S3 이미지 삭제
    """
    try:
        db.delete_travel_image_by_district(district_id)
        db.delete_travel_place_by_district(district_id)
        db.delete_district(district_id)

        db.conn.commit()

        s3.delete_objects_by_district(district_id)

        logger.info(f'district_id {district_id}번 데이터 삭제 완료')

    except Exception:
        db.conn.rollback()
        logger.exception(f'district_id {district_id}번 데이터 삭제 실패')