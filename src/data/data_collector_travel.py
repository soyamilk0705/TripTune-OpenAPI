from .data_collector_image import *
from api.api_handler import *
from utils.utils import *
from utils.log_handler import setup_logger
from utils.config import *
from db.db_handler import DatabaseHandler
from model.travel_place import TravelPlace
from model.location import Location
from db import travel_place_db, area_db, content_type_db, travel_image_db


logger = setup_logger()


def save_travel_places(db : DatabaseHandler, 
                       s3 : S3Handler, 
                       city : str, 
                       district : str, 
                       target_content_name : str, 
                       target_count : int):
    '''
    파라미터로 전달된 지역 정보와 DB에 저장된 컨텐츠 타입을 이용해 특정 지역의 관광지를 조회하고 저장한다.
    관광지 정보, 해당 관광지에 대한 소개 정보, 썸네일 이미지 등을 저장하는 기능을 한다.
    이미지 파일의 경우 S3에 이미지 파일로 저장된다.
    저장 위치: travel_place

    *if문을 추가해 저장되는 데이터 갯수를 제한했다.
    - /areaBasedList1
    - /detailCommon1
    - /detailIntro1
    - /detailImage1
    
    '''
    url = BASE_URL + '/areaBasedList1'
    params = build_params()

    # 지역 조회
    korea_area = area_db.get_area('대한민국', city, district)

    if not korea_area:
        logger.error(f'지역 정보가 존재하지 않습니다 - {city}, {district}')
        return


    # 컨텐츠 타입 조회
    content_type = content_type_db.get_api_content_type(target_content_name)
    
    location = Location(korea_area['country_id'], korea_area['city_id'], korea_area['district_id'])

    params['contentTypeId'] = content_type['api_content_type_id']
    params['lDongRegnCd'] = korea_area['api_city_code']
    params['lDongSignguCd'] = korea_area['api_district_code']

    items = fetch_api_items(url, params)

    total_count = len(items)
    logger.info(f'총 데이터 개수 - {total_count}개')

    if not items:
        logger.info(f'[{city} {district} {target_content_name}] 조회된 관광지 데이터가 없습니다.')
        return

    result = process_travel_places(
        db,
        s3,
        items,
        location,
        content_type,
        target_count
    )

    logger.info('======================================================================')
    logger.info(f'''
                [{city} {district} {target_content_name} 수집 완료] 
                
                전체 관광지 : {total_count}개 
                수집 데이터 : {result['processed']}개
                신규 저장 : {result['insert']}개
                수정 데이터 : {result['update']}개
                변경 없음 : {result['skip']}개
                '''
    )


def process_travel_places(db : DatabaseHandler, 
                          s3 : S3Handler,
                          items : dict,
                          location : Location, 
                          content_type : dict, 
                          target_count : int):
    
    '''
    1. place 조회(DB)
    2. API 수정시간 비교
    3. 변경된 place거나 신규인 경우 상세 정보 조회(API)

    4. place가 없으면
        4.1 place insert
        4.2 썸네일 저장
        4.3 상세 이미지 조회(API)
        4.4 상세 이미지 저장

    5. place가 있으면
        5.1 api_updated_at == modifiedtime
            - 아무것도 안함
        5.2 api_updated_at != modifiedtime
            5.2.1. place update
            5.2.2. 썸네일 비교
                - 다름 → 기존 삭제 후 새로 저장   
            5.2.3 상세 이미지 조회(API)
                - 기존 상세 이미지 삭제
                - 상세 이미지 저장
    '''
    
    # 총 저장된 데이터 갯수 확인
    result = {
        'processed' : 0,
        'insert' : 0,
        'update' : 0,
        'skip' : 0
    }
    now = datetime.now()

    for item in items:
        if result['proceesed'] >= target_count:
            break

        saved_place = travel_place_db.get_travel_place(item['contentid'])

        api_updated_at = convert_to_datetime(item['modifiedtime'])

        # 변경없는 데이터
        if saved_place and saved_place['api_updated_at'] == api_updated_at:
            result['skip'] += 1
            continue
        
        # ---------- 관광지 소개 정보 조회 ----------
        details = get_travel_place_detail(item['contentid'])
        if details['description'] is None:
            continue

        # ---------- 관광지 기본 정보 조회 ----------
        info = get_travel_place_info(
            content_type['api_content_type_id'], 
            item['contentid']
        )

        travel_place = create_travel_place(item, details, info, location, content_type) 
       
        if saved_place is None:
            save_new_travel_place(db, s3, item, travel_place, now)
            result['insert'] += 1
        else: 
            sync_travel_place(db, s3, item, travel_place, saved_place, now)
            result['update'] += 1
        
        result['processed'] += 1
        logger.info('-------------------------------------------------------------------')
        logger.info(f'{result['processed']} 개 데이터 저장 완료')
    
    return result



def get_travel_place_detail(api_content_id : int):
    '''
    특정 관광지에 대한 소개 정보(description)와 홈페이지 정보(<a> 태그로 시작하는 홈페이지 주소)를 조회하고 저장한다.
    저장 위치 : travel_place.description

    '''
    url = BASE_URL + '/detailCommon1'
    params = build_detail_params()

    params['contentId'] = api_content_id
    details = {'description': None, 'homepage': None}

    items = fetch_api_items(url, params)

    if not items:
        return details

    for item in items:
        description = item['overview'].strip()

        if description in ['', '-']:
            return details
        
        details['description'] = description

        homepage = item['homepage'].strip()
       
        if homepage not in ['', '-']:
            start_index = homepage.find('<a ')
            if start_index != -1:
                details['homepage'] = homepage[start_index:]

    logger.info(f'korea_travel_place_detail() - {api_content_id} 관광지 설명 데이터 조회 완료')
    return details


def get_travel_place_info(api_content_type_id : int, api_content_id : int):
    '''
    콘텐츠 타입에 따른 관광지 정보(전화번호, 이용시간, 체크인 시간, 체크아웃 시간)를 조회한다.
    저장 위치 : travel_place.phone_number, travel_place.use_time, travel_place.check_in_time, travel_place.check_out_time

    '''

    url = BASE_URL + '/detailIntro1'
    params = build_params()

    params['contentId'] = api_content_id
    params['contentTypeId'] = api_content_type_id

    info = {
        'phone_number': None,
        'use_time': None,
        'check_in_time': None,
        'check_out_time': None
    }

    items = fetch_api_items(url, params)

    if not items:
        return info

    item = items[0]
   
    if api_content_type_id == 12:   # 관광지
        info['phone_number'] = item['infocenter'] or None
        info['use_time'] = item['usetime'] or None
    elif api_content_type_id == 14: # 문화시설
        info['phone_number'] = item['infocenterculture'] or None
        info['use_time'] = item['usetimeculture'] or None 
    elif api_content_type_id == 28: # 레포츠
        info['phone_number'] = item['infocenterleports'] or None
        info['use_time'] = item['usetimeleports'] or None 
    elif api_content_type_id == 32: # 숙박
        info['phone_number'] = item['infocenterlodging'] or None
        info['check_in_time'] = item['checkintime'] or None
        info['check_out_time'] = item['checkouttime'] or None
    elif api_content_type_id == 38: # 쇼핑      
        info['phone_number'] = item['infocentershopping'] or None
        info['use_time'] = item['opentime'] or None 
    elif api_content_type_id == 39: # 음식점
        info['phone_number'] = item['infocenterfood'] or None
        info['use_time'] = item['opentimefood'] or None 


    logger.info(f'korea_travel_place_info() - {api_content_id} 관광지 전화번호, 이용시간 데이터 조회 완료')
    return info


def create_travel_place(item : dict, 
                        details : dict, 
                        info : dict, 
                        location : Location, 
                        content_type : dict):
    return TravelPlace(
            location=location,
            content_type_id=content_type['content_type_id'],
            place_name=item['title'],
            address=item['addr1'],
            api_content_id=item['contentid'],
            api_created_at=convert_to_datetime(item['createdtime']),
            api_updated_at=convert_to_datetime(item['modifiedtime']),
            created_at=None,
            updated_at=None,
            detail_address=item['addr2'] or None,
            use_time=info['use_time'],
            check_in_time=info['check_in_time'],
            check_out_time=info['check_out_time'],
            homepage=details['homepage'],
            phone_number=info['phone_number'],
            longitude=item['mapx'],
            latitude=item['mapy'],
            description=details['description']
        )


def save_new_travel_place(db : DatabaseHandler,
                          s3 : S3Handler,
                          item : dict,
                          travel_place : TravelPlace,
                          now : datetime):
    
    travel_place.created_at = now
    travel_place.updated_at = now
    travel_place_db.insert_travel_place(travel_place)
    travel_place.place_id = db.get_last_inserted_id()

    # ---------- 썸네일 이미지 저장 ----------
    if item['firstimage']:
        save_travel_image(db, s3, travel_place, item['firstimage'], True)

    save_travel_detail_images(db, s3, travel_place)



def sync_travel_place(db : DatabaseHandler,
                      s3 : S3Handler,
                      item : dict,
                      travel_place : TravelPlace,
                      saved_place : dict,
                      now : datetime):
    travel_place.place_id = saved_place['place_id']
    travel_place.updated_at = now
    travel_place_db.update_travel_place(travel_place)

    # ---------- 썸네일 이미지 저장 ----------
    if item['firstimage']:
        sync_thumbnail_travel_image(db, s3, travel_place, item['firstimage'])
    else:
        thumbnail_image = travel_image_db.get_travel_thumbnail_image(saved_place['place_id'])
        
        if thumbnail_image:
            s3.delete_object(thumbnail_image['object_key'])
            travel_image_db.delete_travel_thumbnail_image(saved_place['place_id'])
        
    sync_travel_detail_images(db, s3, travel_place)


