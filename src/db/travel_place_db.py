from db.db_handler import DatabaseHandler
from model.travel_place import TravelPlace

def travel_place_exists(db : DatabaseHandler, api_content_id : int):
    query = 'SELECT EXISTS (SELECT 1 FROM travel_place WHERE api_content_id = %s)'
    result = db.execute_fetch_one(query, (api_content_id,))

    if result:
        return list(result.values())[0]  # 딕셔너리의 첫 번째 값 반환
    return 0


def get_travel_place(db : DatabaseHandler, api_content_id : int):
    query = '''
        SELECT *
        FROM travel_place
        WHERE api_content_id = %s
    '''
    return db.execute_fetch_one(query, (api_content_id,))


def get_empty_description_travel_place(db : DatabaseHandler):
    query = '''
        SELECT *
        FROM travel_place tp
        LEFT JOIN travel_image ti
        ON tp.place_id = ti.place_id
        WHERE tp.description = '-'
        OR tp.description IS NULL
        OR tp.description = ''
    '''
    return db.execute_fetch_all(query)

def insert_travel_place(db : DatabaseHandler, travel_place : TravelPlace):
    query = '''
        INSERT INTO travel_place(
            country_id,
            city_id,
            district_id,
            content_type_id,
            place_name,
            address,
            api_content_id,
            api_created_at,
            api_updated_at,
            created_at,
            updated_at,
            detail_address,
            use_time,
            check_in_time,
            check_out_time,
            homepage,
            phone_number,
            longitude,
            latitude,
            description
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
    '''

    db.execute_insert(query, (
        travel_place.location.country_id,
        travel_place.location.city_id,
        travel_place.location.district_id,
        travel_place.content_type_id,
        travel_place.place_name,
        travel_place.address,
        travel_place.api_content_id,
        travel_place.api_created_at,
        travel_place.api_updated_at,
        travel_place.created_at,
        travel_place.updated_at,
        travel_place.detail_address,
        travel_place.use_time,
        travel_place.check_in_time,
        travel_place.check_out_time,
        travel_place.homepage,
        travel_place.phone_number,
        travel_place.longitude,
        travel_place.latitude,
        travel_place.description,
    ))



def update_travel_place(db : DatabaseHandler, travel_place : TravelPlace):
    query = '''
        UPDATE travel_place
        SET place_name = %s,
            address = %s,
            api_created_at = %s,
            api_updated_at = %s,
            updated_at = %s,
            detail_address = %s,
            use_time = %s,
            check_in_time = %s,
            check_out_time = %s,
            homepage = %s,
            phone_number = %s,
            longitude = %s,
            latitude = %s,
            description = %s
        WHERE place_id = %s
    '''

    db.execute_update(query, (
        travel_place.place_name,
        travel_place.address,
        travel_place.api_created_at,
        travel_place.api_updated_at,
        travel_place.updated_at,
        travel_place.detail_address,
        travel_place.use_time,
        travel_place.check_in_time,
        travel_place.check_out_time,
        travel_place.homepage,
        travel_place.phone_number,
        travel_place.longitude,
        travel_place.latitude,
        travel_place.description,
        travel_place.place_id,
    ))


def delete_travel_place(db : DatabaseHandler, place_id : int):
    query = '''
        DELETE FROM travel_place 
        WHERE place_id = %s
    '''
    db.execute_delete(query, (place_id,))


def delete_travel_place_by_district(db : DatabaseHandler, district_id : int):
    query = '''
        DELETE FROM travel_place
        WHERE travel_place.district_id = %s
    '''
    db.cursor.execute(query, (district_id,))