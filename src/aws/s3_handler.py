import boto3
from utils.log_handler import setup_logger

logger = setup_logger()

class S3Handler:
    def __init__(self, region_name, bucket_name, aws_access_key_id, aws_secret_access_key):
        try:
            self.s3 = boto3.client(
                service_name = 's3',
                region_name = region_name,
                aws_access_key_id = aws_access_key_id,
                aws_secret_access_key = aws_secret_access_key,
            )
            self.bucket_name = bucket_name
            self.region_name = region_name

            logger.info('s3 bucket 연결 완료!')
        except Exception as e:
            logger.error('s3 연결 실패 : ', e)
            
    def upload_file(self, image_byte_arr, object_key):
        try:
            self.s3.upload_fileobj(image_byte_arr, self.bucket_name, object_key)
        except Exception as e:
            logger.error('업로드 실패 : ', e)

    def delete_all_objects(self):
        try:
            s3 = boto3.resource('s3')
            bucket = s3.Bucket(self.bucket_name)
            bucket.objects.all().delete()

            logger.info(f'{self.bucket_name}의 전체 데이터 삭제 완료')
        except Exception as e:
            logger.error('삭제 실패 : ', e)

    def delete_object(self, object_key):
        try:
            response = self.s3.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f'{object_key} 삭제 완료: {response}')
        except Exception as e:
            logger.error(f'{object_key} 삭제 실패: {e}')
            