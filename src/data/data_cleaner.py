import time
from db import travel_place_db, travel_image_db
from aws.s3_handler import S3Handler
from utils.log_handler import setup_logger
from db.db_handler import DatabaseHandler
from utils.utils import clean_use_time

logger = setup_logger()

def delete_ambiguous_description_data(db : DatabaseHandler, s3 : S3Handler):
    """
    DB 에 저장된 데이터 중 상세설명이 없는 여행지 삭제
    """
    shopping_places = travel_place_db.get_empty_description_travel_place(db)
    logger.info(f"{len(shopping_places)} 개 데이터 조회 완료")

    for place in shopping_places:
        place_id = place['place_id']
        image_id = place['travel_image_id']
        s3_object_key = place['s3_object_key']
        
        try:
            try:
                s3.delete_object(s3_object_key)
            except Exception:
                logger.exception(f"S3 삭제 실패 (place_id={place_id})")
                continue

            travel_image_db.delete_travel_image(db, image_id)

            time.sleep(0.1)

            travel_place_db.delete_travel_place(db, place_id)

            db.commit()

            logger.info(f"(place_id={place_id}) 여행지 데이터 삭제 완료")
        except Exception:
            db.rollback()
            logger.exception(f"삭제 중 오류 발생 (place_id={place_id})")


def clean_saved_use_time(db: DatabaseHandler, start: int, end: int):
    """
    DB에 저장된 여행지 이용시간 띄어쓰기 정제
    """
    places = travel_place_db.get_travel_places(db, start, end)

    updated_count = 0

    for place in places:
        original = place.get('use_time')
        clean_data = clean_use_time(original)

        # 1. 변경사항이 없는 경우 DB UPDATE 생략
        if original == clean_data:
            continue

        # 2. 변경된 경우에만 DB 업데이트
        travel_place_db.update_use_time(db, place['place_id'], clean_data)
        updated_count += 1

        logger.info(
            f"\n==============[place_id={place['place_id']}]==============\n"
            f"BEFORE:\n"
            f"{original}\n"
            f"AFTER:\n"
            f"{clean_data}"
        )

    logger.info(f"=== 정제 완료: 총 {len(places)}개 중 {updated_count}개 업데이트됨 ===")