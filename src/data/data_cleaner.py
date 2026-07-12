from aws.s3_handler import S3Handler
from utils.log_handler import setup_logger
from db.db_handler import DatabaseHandler
import time
from db import travel_place_db, travel_image_db

logger = setup_logger()

def delete_ambiguous_description_data(db : DatabaseHandler, s3 : S3Handler):
    shopping_places = travel_place_db.get_empty_description_travel_place(db)
    logger.info(f'{len(shopping_places)} 개 데이터 조회 완료')

    for place in shopping_places:
        place_id = place['place_id']
        image_id = place['travel_image_id']
        object_key = place['s3_object_key']
        
        try:
            try:
                s3.delete_object(object_key)
            except:
                logger.error(f'S3 삭제 실패 (place_id={place_id}): {e}')
                break

            travel_image_db.delete_travel_image(db, image_id)

            time.sleep(0.1)

            travel_place_db.delete_travel_place(db, place_id)

            logger.info(f'(place_id={place_id}) 여행지 데이터 삭제 완료')
        except Exception:
            logger.exception(f'삭제 중 오류 발생 (place_id={place_id})')