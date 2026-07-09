import boto3
from utils.log_handler import setup_logger

logger = setup_logger()

class S3Handler:
    def __init__(self, region_name, bucket_name, aws_access_key_id, aws_secret_access_key):
        try:
            # 파일 업로드/삭제용
            self.s3_client = boto3.client(
                service_name = 's3',
                region_name = region_name,
                aws_access_key_id = aws_access_key_id,
                aws_secret_access_key = aws_secret_access_key,
            )

            # Prefix(폴더) 단위 작업용
            self.s3_resource = boto3.resource(
                service_name = 's3',
                region_name = region_name,
                aws_access_key_id = aws_access_key_id,
                aws_secret_access_key = aws_secret_access_key,
            )

            self.bucket_name = bucket_name

            logger.info('s3 bucket 연결 완료!')
        except Exception:
            logger.exception(f's3 연결 실패')
            
    def upload_file(self, image_byte_arr, object_key):
        try:
            self.s3_client.upload_fileobj(
                Fileobj=image_byte_arr,
                Bucket=self.bucket_name, 
                Key=object_key
            )
            logger.info(f'{object_key} 업로드 완료')
        except Exception as e:
            logger.exception(f'{object_key} 업로드 실패')


    def delete_object(self, object_key):
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )

            logger.info(f'{object_key} 삭제 완료')
        except Exception:
            logger.exception(f'{object_key} 삭제 실패')
            
    
    def delete_objects_by_district(self, district_id):
        prefix = f'img/korea/{district_id}/'

        try:
            bucket = self.s3_resource.Bucket(self.bucket_name)
            bucket.objects.filter(Prefix=prefix).delete()

            logger.info(f'{prefix} 이미지 삭제 완료')
        except Exception:
            logger.exception(f'{prefix} 이미지 삭제 실패')


    def delete_all_objects(self):
        try:
            bucket = self.s3_resource.Bucket(self.bucket_name)
            bucket.objects.all().delete()

            logger.info(f'{self.bucket_name}의 전체 데이터 삭제 완료')
        except Exception:
            logger.exception(f'전체 이미지 삭제 실패')