import os
from dotenv import load_dotenv
from db.db_handler import DatabaseHandler
from data.data_collector_image import *
from data.data_collector_area import *
from data.data_collector_travel import *
from data.data_cleaner import *
from aws.s3_handler import *


def main():
    load_dotenv()

    # database
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    db_port = int(os.getenv('DB_PORT'))

    # s3
    s3_region_name = os.getenv('S3_REGION')
    s3_bucket_name = os.getenv('S3_BUCKET_NAME')
    aws_accees_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

    if not all([db_host, db_user, db_password, db_name, db_port, s3_region_name, s3_bucket_name, aws_accees_key_id, aws_secret_access_key]):
        print('환경 변수 불러오기 실패')
        return None


    db = DatabaseHandler(db_host, db_user, db_password, db_name, db_port)
    s3 = S3Handler(s3_region_name, s3_bucket_name, aws_accees_key_id, aws_secret_access_key)
    
    try:
        # korea_city_code(db)
        # korea_district_code(db)

        # limited_korea_travel_places(db, s3, '강원특별자치도', '철원군', '음식점', 30)
        # delete_ambiguous_description_data(db, s3)

        delete_district_data(db, s3, 107)

    finally:
        db.close()



if __name__ == '__main__':
    main()
