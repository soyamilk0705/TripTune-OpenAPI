from db.db_handler import DatabaseHandler
from model.travel_image import TravelImage

def get_travel_thumbnail_image(db : DatabaseHandler, place_id : int):
    query = '''
        SELECT *
        FROM travel_image
        WHERE place_id = %s AND is_thumbnail = TRUE 
    '''

    return db.execute_fetch_one(query, (place_id,))


def get_travel_detail_images(db : DatabaseHandler, place_id : int):
    query = '''
        SELECT *
        FROM travel_image
        WHERE place_id = %s AND is_thumbnail = FALSE 
    '''

    return db.execute_fetch_all(query, (place_id,))


def insert_travel_image(db : DatabaseHandler, travel_image : TravelImage):
    query = '''
        INSERT INTO travel_image(
            place_id,
            s3_object_key,
            original_name, 
            file_name, 
            file_type, 
            file_size, 
            created_at, 
            updated_at,
            is_thumbnail, 
            api_file_url,
            serial_number
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''

    db.execute_insert(query, (
        travel_image.place_id,
        travel_image.s3_object_key,
        travel_image.original_name, 
        travel_image.file_name, 
        travel_image.file_type, 
        travel_image.file_size, 
        travel_image.created_at,
        travel_image.updated_at,
        travel_image.is_thumbnail, 
        travel_image.api_file_url,
        travel_image.serial_number,
    ))



def update_travel_image(db : DatabaseHandler, travel_image : TravelImage):
    query = '''
        UPDATE travel_image
        SET s3_object_key = %s,
            original_name = %s, 
            file_name = %s, 
            file_type = %s,
            file_size = %s, 
            created_at = %s, 
            is_thumbnail = %s, 
            api_file_url = %s,
            serial_number = %s
        WHERE travel_image_id = %s
    '''

    db.execute_update(query, (
        travel_image.s3_object_key,
        travel_image.original_name, 
        travel_image.file_name, 
        travel_image.file_type, 
        travel_image.file_size, 
        travel_image.created_at, 
        travel_image.is_thumbnail, 
        travel_image.api_file_url,
        travel_image.serial_number,
        travel_image.travel_image_id,
    ))


def delete_travel_image_by_district(db : DatabaseHandler, district_id : int):
    query = '''
        DELETE ti 
        FROM travel_image ti
        JOIN travel_place tp
        ON ti.place_id = tp.place_id
        WHERE tp.district_id = %s
    '''
    db.cursor.execute(query, (district_id,))


def delete_travel_image(db : DatabaseHandler, travel_image_id : int):
    query = '''
        DELETE FROM travel_image
        WHERE travel_image_id = %s
    '''

    db.cursor.execute(query, (travel_image_id,))


def delete_travel_thumbnail_image(db : DatabaseHandler, travel_image_id : int):
    query = '''
        DELETE FROM travel_image
        WHERE travel_image_id = %s AND is_thumbnail = TRUE
    '''
    db.cursor.execute(query, (travel_image_id,))


def delete_travel_detail_images(db : DatabaseHandler, travel_image_id : int):
    query = '''
        DELETE FROM travel_image
        WHERE travel_image_id = %s AND is_thumbnail = FALSE
    '''
    db.cursor.execute(query, (travel_image_id,))