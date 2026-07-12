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

    # ---------------------------------------------------------
    # 범용 쿼리 실행기 (execute_*) : 쿼리 문자열을 외부에서 받아 그대로 실행
    # ---------------------------------------------------------
    
    
    def execute_fetch_all(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def execute_fetch_one(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def execute_insert(self, query, params):
        self.cursor.execute(query, params)
        self.conn.commit()


    def execute_update(self, query, params):
        self.cursor.execute(query, params)
        self.conn.commit()


    def get_last_inserted_id(self):
        return self.cursor.lastrowid
    

    def execute_delete(self, query, params):
        self.cursor.execute(query, params)
        self.conn.commit()


    def close(self):
        self.conn.close()
    

    # ---------------------------------------------------------
    # 특정 비즈니스 로직 메소드
    # ---------------------------------------------------------

    def travel_place_exists(self, params=None):
        exist_query = 'SELECT EXISTS (SELECT 1 FROM travel_place WHERE api_content_id = %s)'
        self.cursor.execute(exist_query, params)
        result = self.cursor.fetchone()

        if result:
            return list(result.values())[0]  # 딕셔너리의 첫 번째 값 반환
        return 0


    def get_area(self, country, city, district):
        select_city_and_district = '''SELECT
                                        ct.country_id, ct.country_name,
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
                                
        self.cursor.execute(select_city_and_district, (country, city, district))
        return self.cursor.fetchone()

    def get_areas(self):
        select_city_and_district = '''SELECT
                                    ct.country_id, ct.country_name,
                                    c.city_id, c.city_name, c.api_city_code,
                                    d.district_id, d.district_name, d.api_district_code
                                FROM district d
                                INNER JOIN city c
                                ON d.city_id = c.city_id
                                INNER JOIN country ct
                                ON c.country_id = ct.country_id
                                '''
        self.cursor.execute(select_city_and_district)
        return self.cursor.fetchall()
    

    def get_api_content_type(self, content_type_name):
        select_api_content_type = """
            SELECT * 
            FROM api_content_type 
            WHERE content_type_name = %s
        """

        self.cursor.execute(select_api_content_type, (content_type_name,))


    def get_travel_place(self, api_content_id):
        select_travel_place = """
            SELECT *
            FROM travel_place
            WHERE api_content_id = %s
        """

        self.cursor.execute(select_travel_place, (api_content_id,))
        return self.cursor.fetchone()
    
    
    def get_travel_thumbnail_image(self, place_id):
        select_travel_images = """
            SELECT *
            FROM travel_image
            WHERE place_id = %s and is_thumbnail = true 
        """

        self.cursor.execute(select_travel_images, (place_id,))
        return self.cursor.fetchone()


    def get_travel_detail_images(self, place_id):
        select_travel_images = """
            SELECT *
            FROM travel_image
            WHERE place_id = %s and is_thumbnail = false 
        """

        self.cursor.execute(select_travel_images, (place_id,))
        return self.cursor.fetchall()


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
                                serial_number
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            travel_image.api_file_url,
            travel_image.serial_number
        ))
        
        self.conn.commit()

    
    def update_travel_place(self, travel_place):
        update_travel_place = '''
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

        self.cursor.execute(update_travel_place, (
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
            travel_place.place_id
        ))
        
        self.conn.commit()


    def update_travel_image(self, travel_image):
        update_travel_image = '''
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

        self.cursor.execute(update_travel_image, (
            travel_image.place_id,
            travel_image.s3_object_key,
            travel_image.original_name, 
            travel_image.file_name, 
            travel_image.file_type, 
            travel_image.file_size, 
            travel_image.created_at, 
            travel_image.is_thumbnail, 
            travel_image.api_file_url,
            travel_image.serial_number,
            travel_image.travel_image_id
        ))
        
        self.conn.commit()



    def delete_district(self, district_id):
        delete_district = """
            DELETE FROM district
            WHERE district.district_id = %s
        """
        self.cursor.execute(delete_district, (district_id,))
        self.conn.commit()

    def delete_travel_place_by_district(self, district_id):
        delete_travel_place = """
            DELETE FROM travel_place
            WHERE travel_place.district_id = %s
        """
        self.cursor.execute(delete_travel_place, (district_id,))
        

    def delete_travel_image_by_district(self, district_id):
        delete_travel_image = """
            DELETE ti
            FROM travel_image ti
            JOIN travel_place tp
            ON ti.place_id = tp.place_id
            WHERE tp.district_id = %s
        """
        self.cursor.execute(delete_travel_image, (district_id,))

    
    def delete_travel_image(self, travel_image_id):
        delete_travel_image = """
        DELETE FROM travel_image
        WHERE travel_image_id = %s
        """
        self.cursor.execute(delete_travel_image, (travel_image_id,))
    

    def delete_travel_thumbnail_image(self, place_id):
        delete_detail_image = """
        DELETE FROM travel_image
        WHERE place_id = %s AND is_thumbnail = true
        """
        self.cursor.execute(delete_detail_image, (place_id,))


    def delete_travel_detail_images(self, place_id):
        delete_detail_image = """
        DELETE FROM travel_image
        WHERE place_id = %s AND is_thumbnail = false
        """
        self.cursor.execute(delete_detail_image, (place_id,))