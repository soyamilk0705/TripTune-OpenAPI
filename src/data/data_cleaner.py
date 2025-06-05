from aws.s3_handler import *
from utils.log_handler import setup_logger
import time

logger = setup_logger()

def delete_ambiguous_description_data(db, s3):
    query = '''
        SELECT *
        FROM travel_place tp
        LEFT JOIN travel_image ti
        ON tp.place_id = ti.place_id
        WHERE tp.description = '-'
        OR tp.description IS NULL
        OR tp.description = ''
    '''

    shopping_places = db.execute_select_all(query)

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
                break;
        
            db.execute_delete(
                'DELETE FROM travel_image WHERE travel_image_id = %s'
                , (image_id,)
            )

            time.sleep(0.1)

            db.execute_delete(
                'DELETE FROM travel_place WHERE place_id = %s'
                , (place_id,)
            )

            logger.info(f'(place_id={place_id}) 여행지 데이터 삭제 완료')
        except Exception as e:
            logger.error(f'삭제 중 오류 발생 (place_id={place_id}): {e}')