import os
from dotenv import load_dotenv
from aws.s3_handler import S3Handler
from data.data_cleaner import clean_saved_use_time
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

    # ssh
    ssh_host = os.getenv('SSH_HOST')
    ssh_port = int(os.getenv('SSH_PORT'))
    ssh_username = os.getenv('SSH_USERNAME')
    ssh_pkey = os.getenv('SSH_PKEY')

    # s3
    s3_region_name = os.getenv('S3_REGION')
    s3_bucket_name = os.getenv('S3_BUCKET_NAME')
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')


    db_config = [db_host, db_user, db_password, db_name, db_port]
    ssh_config = [ssh_host, ssh_port, ssh_username, ssh_pkey]
    s3_config = [s3_region_name, s3_bucket_name, aws_access_key_id, aws_secret_access_key]

    if not all(db_config + ssh_config + s3_config):
        print("환경 변수 불러오기 실패")
        return


    db = DatabaseHandler(
        db_host=db_host,
        db_user=db_user,
        db_password=db_password,
        db=db_name,
        db_port=db_port,
        ssh_host=ssh_host,
        ssh_port=ssh_port,
        ssh_username=ssh_username,
        ssh_pkey=ssh_pkey
    )

    s3 = S3Handler(
        region_name=s3_region_name,
        bucket_name=s3_bucket_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    
    try:
        # target_place_count 는 10 단위로 요청
        # 관광지
        # 문화시설
        # 레포츠
        # 숙박
        # 쇼핑
        # 음식점
        save_travel_places(db, s3, '경기도', '이천시', '레포츠', 50)

    finally:
        db.close()



if __name__ == '__main__':
    main()
