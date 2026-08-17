from datetime import datetime
from math import ceil

from api.api_handler import fetch_page_api_items, fetch_first_page_api_items
from aws.s3_handler import S3Handler
from utils.config import BASE_URL, build_params, build_detail_params, NUM_OF_ROWS
from utils.log_handler import setup_logger
from db.db_handler import DatabaseHandler
from model.travel_place import TravelPlace
from model.location import Location
from db import travel_place_db, area_db, content_type_db, travel_image_db
from utils.utils import convert_to_datetime, clean_use_time
from data.data_collector_image import save_travel_image, sync_thumbnail_travel_image, sync_travel_detail_images, \
    save_travel_detail_images

logger = setup_logger()


def save_travel_places(db : DatabaseHandler,
                       s3 : S3Handler, 
                       city : str, 
                       district : str, 
                       target_content_name : str, 
                       target_place_count : int):
    """
    파라미터로 전달된 지역 정보와 DB에 저장된 컨텐츠 타입을 이용해 특정 지역의 여행지를 조회하고 저장한다.
    여행지 정보, 해당 여행지에 대한 소개 정보, 썸네일 이미지 등을 저장하는 기능을 한다.
    이미지 파일의 경우 S3에 이미지 파일로 저장된다.
    저장 위치: travel_place

    *if문을 추가해 저장되는 데이터 갯수를 제한했다.
    - /areaBasedList1
    - /detailCommon1
    - /detailIntro1
    - /detailImage1

    """
    url = BASE_URL + '/areaBasedList2'
    params = build_params()

    # 지역 조회
    korea_area = area_db.get_area(db, '대한민국', city, district)

    if not korea_area:
        logger.exception(f"{city}, {district} - 지역 정보 존재 안함")
        return

    # 컨텐츠 타입 조회
    content_type = content_type_db.get_api_content_type(db, target_content_name)
    
    location = Location(korea_area['country_id'], korea_area['city_id'], korea_area['district_id'])

    params['contentTypeId'] = content_type['api_content_type_id']
    params['lDongRegnCd'] = korea_area['api_city_code']
    params['lDongSignguCd'] = korea_area['api_district_code']

    total_result = {
        'insert': 0,
        'update': 0,
        'skip': 0
    }

    # ==========================
    # 첫 페이지 요청
    # ==========================
    items, total_count = fetch_page_api_items(url, params, 1)

    if not items:
        logger.info(f"{city} {district} {target_content_name} - 조회된 데이터가 없음")
        return

    # 전체 여행지 기준 마지막 페이지 계산
    last_page = ceil(total_count / NUM_OF_ROWS)
    saved_count = 0

    # ==========================
    # 필요한 페이지 요청
    # ==========================
    for page_no in range(1, last_page + 1):

        if saved_count >= target_place_count:
            logger.info(f"목표 저장 개수 {target_place_count} 개 달성으로 조기 종료")
            break

        # 첫 페이지는 이미 요청했으므로 재요청 안함
        if page_no != 1:
            items, _ = fetch_page_api_items(url, params, page_no)
            if not items:
                break

        # 남은 데이터 갯수
        remain_count = target_place_count - saved_count

        result = process_travel_places(
            db,
            s3,
            items,
            location,
            content_type,
            remain_count
        )

        for key in total_result:
            total_result[key] += result[key]

        # 실제 변경/저장된 개수
        saved_count += (result['insert'] + result['update'])

    logger.info("======================================================================")
    logger.info(f"""
                [{city} {district} {target_content_name} 수집 완료] 
                
                전체 여행지 : {total_count}개
                목표 저장 : {target_place_count}개
                저장/수정 완료 : {saved_count}개
                신규 저장 : {total_result['insert']}개
                수정 : {total_result['update']}개
                변경 없음 : {total_result['skip']}개
                """
    )
    logger.info("======================================================================")


def process_travel_places(db : DatabaseHandler, 
                          s3 : S3Handler,
                          items : dict,
                          location : Location, 
                          content_type : dict,
                          remain_count : int):

    """
    1. 위도/경도 데이터 없으면 pass
    2. place 조회(DB)
    3. API 수정시간 비교
        3.1. 저장된 place가 있고 수정 시간이 변경되지 않았다면 pass
        3.2. 변경된 place거나 신규인 경우 상세 정보 조회(API)
            - 신규 → 4번(place 신규 저장) 진행
            - 변경된 place → 5번(place 갱신) 진행

    4. place 신규 저장
        4.1. place insert
        4.2. 썸네일 저장
        4.3. 상세 이미지 조회(API)
        4.4. 상세 이미지 저장

    5. place 갱신
        5.1. place update
        5.2. 썸네일 비교
            - 다름 → 새로 저장 후 기존 삭제
            - 같음 → pass
        5.3. 상세 이미지 조회(API)
            - 상세 이미지 저장
            - 기존 상세 이미지 삭제
    """
    
    # 총 저장된 데이터 갯수 확인
    result = {
        'insert': 0,
        'update': 0,
        'skip': 0
    }
    now = datetime.now()

    for item in items:
        # 목표 갯수 달성
        if remain_count <= 0:
            break

        # 위도나 경도 데이터가 없으면 pass
        if item['mapx'] in (None, "", "null") or item['mapy'] in (None, "", "null"):
            result['skip'] += 1
            logger.info(f"[SKIP] {item['title']}({item['contentid']} - 위도/경도 데이터 없음")
            continue

        saved_place = travel_place_db.get_travel_place(db, item['contentid'])
        api_updated_at = convert_to_datetime(item['modifiedtime'])

        # 데이터 변경되지 않았으면 pass
        if saved_place and saved_place['api_updated_at'] == api_updated_at:
            result['skip'] += 1
            logger.info(f"[SKIP] {saved_place['place_name']}({item['contentid']}) - 여행지 데이터 변경 없음")
            continue


        logger.info(f"[START] {item['title']}({item['contentid']}) 데이터 수집 시작")

        # ----------------------------
        # 여행지 소개 정보 조회
        # ----------------------------
        details = get_travel_place_detail(item['contentid'])
        logger.info(f"[END] {item['title']}({item['contentid']}) 여행지 설명 데이터 조회 완료")

        if details['description'] is None:
            result['skip'] += 1
            logger.info(f"[SKIP] {item['title']}({item['contentid']}) 여행지 설명 데이터 없어 데이터 수집 제외")
            continue

        # ----------------------------
        # 여행지 기본 정보 조회
        # ----------------------------
        info = get_travel_place_info(
            content_type['api_content_type_id'], 
            item['contentid']
        )
        logger.info(f"[END] {item['title']}({item['contentid']})  여행지 전화번호, 이용시간 데이터 조회 완료")

        travel_place = create_travel_place(item, details, info, location, content_type)

        # ----------------------------
        # 여행지 신규 저장 or 갱신
        # ----------------------------
        if saved_place is None:
            save_new_travel_place(db, s3, item, travel_place, now)
            result['insert'] += 1
        else: 
            sync_travel_place(db, s3, item, travel_place, saved_place, now)
            result['update'] += 1

        remain_count -= 1
        logger.info(f"[END] process_travel_places() 종료")
    
    return result



def get_travel_place_detail(api_content_id : int):
    """
    특정 여행지에 대한 소개 정보(description)와 홈페이지 정보(<a> 태그로 시작하는 홈페이지 주소)를 조회하고 저장한다.
    저장 위치 : travel_place.description

    """
    url = BASE_URL + '/detailCommon2'
    params = build_detail_params()

    params['contentId'] = api_content_id
    details = {'description': None, 'homepage': None}

    items = fetch_first_page_api_items(url, params)

    if not items:
        return details

    item = items[0]

    description = item['overview'].strip()
    if description in ['', '-']:
        return details

    details['description'] = description

    homepage = item['homepage'].strip()
    if homepage not in ['', '-']:
        start_index = homepage.find('<a ')
        if start_index != -1:
            details['homepage'] = homepage[start_index:]

    return details


def get_travel_place_info(api_content_type_id : int, api_content_id : int):
    """
    콘텐츠 타입에 따른 여행지 정보(전화번호, 이용시간, 체크인 시간, 체크아웃 시간)를 조회한다.
    저장 위치 : travel_place.phone_number, travel_place.use_time, travel_place.check_in_time, travel_place.check_out_time

    """

    url = BASE_URL + '/detailIntro2'
    params = build_params()

    params['contentId'] = api_content_id
    params['contentTypeId'] = api_content_type_id

    info = {
        'phone_number': None,
        'use_time': None,
        'check_in_time': None,
        'check_out_time': None
    }

    items = fetch_first_page_api_items(url, params)

    if not items:
        return info

    item = items[0]
   
    if api_content_type_id == 12:   # 관광지
        info['phone_number'] = item['infocenter'] or None
        info['use_time'] = clean_use_time(item['usetime']) or None
    elif api_content_type_id == 14: # 문화시설
        info['phone_number'] = item['infocenterculture'] or None
        info['use_time'] = clean_use_time(item['usetimeculture']) or None
    elif api_content_type_id == 28: # 레포츠
        info['phone_number'] = item['infocenterleports'] or None
        info['use_time'] = clean_use_time(item['usetimeleports']) or None
    elif api_content_type_id == 32: # 숙박
        info['phone_number'] = item['infocenterlodging'] or None
        info['check_in_time'] = item['checkintime'] or None
        info['check_out_time'] = item['checkouttime'] or None
    elif api_content_type_id == 38: # 쇼핑      
        info['phone_number'] = item['infocentershopping'] or None
        info['use_time'] = clean_use_time(item['opentime']) or None
    elif api_content_type_id == 39: # 음식점
        info['phone_number'] = item['infocenterfood'] or None
        info['use_time'] = clean_use_time(item['opentimefood']) or None

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
    """
    신규 여행지, 썸네일 이미지, 상세 이미지를 저장한다.
    예외 발생 시 DB를 롤백 후 s3에 저장된 이미지를 삭제한다.
    """

    # s3에 업로드한 이미지들의 s3_object_key
    uploaded_keys = []

    try:
        logger.info("-------------------------------------------------------------------")
        logger.info(f"[START] {travel_place.place_name}({travel_place.api_content_id}) 여행지 신규 저장 시작")
        travel_place.created_at = now
        travel_place.updated_at = now

        travel_place_db.insert_travel_place(db, travel_place)
        travel_place.place_id = db.get_last_inserted_id()

        # ----------------------------
        # 신규 썸네일 저장
        # ----------------------------
        if item['firstimage']:
            key = save_travel_image(
                db,
                s3,
                travel_place,
                item['firstimage'],
                True,
                None
            )
            uploaded_keys.append(key)

        # ----------------------------
        # 상세 이미지 저장
        # ----------------------------
        uploaded_keys.extend(save_travel_detail_images(db, s3, travel_place))

        db.commit()

        logger.info("-------------------------------------------------------------------")
        logger.info(f"[END] {travel_place.place_name}({travel_place.api_content_id}) 여행지 신규 저장 완료")

    except Exception:
        logger.exception(f"[ERROR] {travel_place.place_id}({travel_place.api_content_id}) 데이터 신규 저장 중 예외 발생으로 rollback")
        db.rollback()

        for key in uploaded_keys:
            s3.delete_object(key)

        raise


def sync_travel_place(db : DatabaseHandler,
                      s3 : S3Handler,
                      item : dict,
                      travel_place : TravelPlace,
                      saved_place : dict,
                      now : datetime):
    """
    API 에서 받은 여행지 데이터에 변경이 있을 시 기존 DB에 저장된 데이터를 수정한다.
    썸네일 이미지 변경이 있을 시에만 수정한다.
    상세 이미지는 신규 저장 후 기존 이미지를 삭제한다.
    예외 발생 시 DB를 롤백하고 s3 이미지를 삭제한다.
    """
    travel_place.place_id = saved_place['place_id']
    travel_place.updated_at = now

    uploaded_keys = []

    try:
        logger.info("-------------------------------------------------------------------")
        logger.info(f"[START] {travel_place.place_name}({travel_place.api_content_id}) 여행지 갱신 시작")
        travel_place_db.update_travel_place(db, travel_place)

        # ----------------------------
        # 썸네일 이미지 갱신
        # ----------------------------
        if item['firstimage']:
            key = sync_thumbnail_travel_image(
                db,
                s3,
                travel_place,
                item['firstimage']
            )

            if key:
                uploaded_keys.append(key)
        else:
            # API 에서 썸네일 이미지가 없는 경우 기존 저장된 데이터 삭제
            thumbnail_image = travel_image_db.get_travel_thumbnail_image(db, saved_place['place_id'])

            if thumbnail_image:
                travel_image_db.delete_travel_thumbnail_image(db, thumbnail_image['travel_image_id'])
                s3.delete_object(thumbnail_image['s3_object_key'])

        # ----------------------------
        # 상세 이미지 갱신: 신규 저장 후 삭제
        # ----------------------------
        detail_uploaded_keys = sync_travel_detail_images(db, s3, travel_place)
        uploaded_keys.extend(detail_uploaded_keys)

        db.commit()
        logger.info(f"[END] {travel_place.place_name}({travel_place.api_content_id}) 여행지 갱신 완료")

    except Exception:
        logger.exception(f"[ERROR] {travel_place.place_id}({travel_place.api_content_id}) 데이터 갱신 중 예외 발생으로 rollback")
        db.rollback()

        # 이번 작업에서 새로 업로드한 이미지 삭제
        for key in uploaded_keys:
            s3.delete_object(key)

        raise


