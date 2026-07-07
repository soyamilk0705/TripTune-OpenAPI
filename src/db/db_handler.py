import pymysql

class DatabaseHandler:
    def __init__(self, host, user, password, db, port):
        self.conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db,
            port=port,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.conn.cursor()

    def execute_exist_travel_place(self, params=None):
        exist_query = 'SELECT EXISTS (SELECT 1 FROM travel_place WHERE api_content_id = %s)'
        self.cursor.execute(exist_query, params)
        result = self.cursor.fetchone()

        if result:
            return list(result.values())[0]  # 딕셔너리의 첫 번째 값 반환
        return 0

    def execute_select_all(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def execute_select_one(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def select_area_one(self, country, city, district):
        select_city_and_district = '''SELECT
                                        ct.country_id, ct.country_name,
                                        c.city_id, c.city_name, c.api_area_code,
                                        d.district_id, d.district_name, d.api_sigungu_code
                                    FROM district d
                                    INNER JOIN city c
                                    ON d.city_id = c.city_id
                                    INNER JOIN country ct
                                    ON c.country_id = ct.country_id
                                    WHERE ct.country_name = %s
                                    AND c.city_name = %s
                                    AND d.district_name = %s
                                    '''
                                
        self.cursor.execute(select_city_and_district, (country, city, district))
        return self.cursor.fetchone()

    def select_area_all(self):
        select_city_and_district = '''SELECT
                                    ct.country_id, ct.country_name,
                                    c.city_id, c.city_name, c.api_area_code,
                                    d.district_id, d.district_name, d.api_sigungu_code
                                FROM district d
                                INNER JOIN city c
                                ON d.city_id = c.city_id
                                INNER JOIN country ct
                                ON c.country_id = ct.country_id
                                '''
        self.cursor.execute(select_city_and_district)
        return self.cursor.fetchall()

    def execute_insert(self, query, params):
        self.cursor.execute(query, params)
        self.conn.commit()


    def insert_travel_place(self, travel_place):

        insert_travel_place = '''
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

        self.cursor.execute(insert_travel_place, (
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
            travel_place.description
        ))
        
        self.conn.commit()

     
    

    def insert_travel_image(self, travel_image):
        insert_travel_image = '''
                            INSERT INTO travel_image(
                                place_id,
                                s3_object_key,
                                original_name, 
                                file_name, 
                                file_type, 
                                file_size, 
                                created_at, 
                                is_thumbnail, 
                                api_file_url
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        '''

        self.cursor.execute(insert_travel_image, (
            travel_image.place_id,
            travel_image.s3_object_key,
            travel_image.original_name, 
            travel_image.file_name, 
            travel_image.file_type, 
            travel_image.file_size, 
            travel_image.created_at, 
            travel_image.is_thumbnail, 
            travel_image.api_file_url
        ))
        
        self.conn.commit()

    def execute_update(self, query, params):
        self.cursor.execute(query, params)
        self.conn.commit()

    def execute_last_inserted_id(self):
        return self.cursor.lastrowid
    

    def execute_delete(self, query, params):
        self.cursor.execute(query, params)
        self.conn.commit()


    def close(self):
        self.conn.close()
    
    