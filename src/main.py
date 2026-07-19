import os
from dotenv import load_dotenv
from aws.s3_handler import S3Handler
from data.data_collector_travel import save_travel_places
from db.db_handler import DatabaseHandler


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
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

    if not all([db_host, db_user, db_password, db_name, db_port, s3_region_name, s3_bucket_name, aws_access_key_id, aws_secret_access_key]):
        print('환경 변수 불러오기 실패')
        return None


    db = DatabaseHandler(db_host, db_user, db_password, db_name, db_port)
    s3 = S3Handler(s3_region_name, s3_bucket_name, aws_access_key_id, aws_secret_access_key)
    
    try:
        # target_place_count 는 10 단위로 요청
        # 관광지
        # 문화시설
        # 레포츠
        # 숙박
        # 쇼핑
        # 음식점
        save_travel_places(db, s3, '서울특별시', '중랑구', '관광지', 30)


    finally:
        db.close()



if __name__ == '__main__':
    main()
