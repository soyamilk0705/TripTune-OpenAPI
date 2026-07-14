from db.db_handler import DatabaseHandler

def get_area(db : DatabaseHandler, country : str, city : str, district : str):
    query = '''
        SELECT ct.country_id, ct.country_name,
            c.city_id, c.city_name, c.api_city_code,
            d.district_id, d.district_name, d.api_district_code
        FROM district d
        INNER JOIN city c
        ON d.city_id = c.city_id
        INNER JOIN country ct
        ON c.country_id = ct.country_id
        WHERE ct.country_name = %s
        AND c.city_name = %s
        AND d.district_name = %s
    '''
                            
    return db.execute_fetch_one(query, (country, city, district))

def get_areas(db : DatabaseHandler):
    query = '''
        SELECT ct.country_id, ct.country_name,
            c.city_id, c.city_name, c.api_city_code,
            d.district_id, d.district_name, d.api_district_code
        FROM district d
        INNER JOIN city c
        ON d.city_id = c.city_id
        INNER JOIN country ct
        ON c.country_id = ct.country_id
    '''
    return db.execute_fetch_all(query)

def get_cities(db : DatabaseHandler):
    query = '''
        SELECT city_id, api_city_code 
        FROM city
    '''
    return db.execute_fetch_all(query)


def get_country_id(db : DatabaseHandler, country_name : str):
    query = '''
        SELECT country_id 
        FROM country 
        WHERE country_name = %s
    '''
    return db.execute_fetch_one(query, (country_name, ))


def insert_city(db : DatabaseHandler, 
                country_id : int,  
                api_city_code : int, 
                city_name : str):
    query = '''
        INSERT INTO city(country_id, api_city_code, city_name) 
        VALUES (%s, %s, %s)
    '''
    db.execute_insert(query, (country_id, api_city_code, city_name))
    db.commit()

def insert_district(db : DatabaseHandler, 
                    city_id : int, 
                    api_district_code : int, 
                    district_name : str):
    query = '''
        INSERT INTO district(city_id, api_district_code, district_name) 
        VALUES (%s, %s, %s)
    '''
    db.execute_insert(query, (city_id, api_district_code, district_name,))
    db.commit()


def delete_district(db : DatabaseHandler, district_id : int):
    query = """
        DELETE FROM district
        WHERE district.district_id = %s
    """
    db.execute_delete(query, (district_id,))

        