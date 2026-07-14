import requests
from utils.log_handler import setup_logger
from datetime import datetime
from PIL import Image
from io import BytesIO

logger = setup_logger()

def convert_to_datetime(date_string : str) -> datetime:
    """
    파라미터로 전달된 data_string(날짜 문자열)을 mysql 에서 사용하는 날짜 데이터 형식인 문자열로 변환한다.

    [Parameter]
    date_string: 날짜 문자열
    """
    return datetime.strptime(date_string, '%Y%m%d%H%M%S')


def download_and_compress_image(image_url : str, quality : int):
    """
    파라미터로 전달된 관광지 이미지 url에서 이미지를 다운로드 한 후 압축한다.

    [Parameter]
    image_url: open api 에서 제공하는 관광지 이미지 url
    quality: 압축 비율

    [Return]
    img_byte_arr: 압축한 이미지 데이터를 메모리에 저장한 BytesIO 객체
    img_size: 압축한 이미지 크기
    """
    response = requests.get(image_url)
    
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content)).convert('RGB')

        # 메모리 내에 BytesIO 객체에 이미지 저장
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, 'JPEG', quality=quality)

        img_byte_arr.seek(0)
        img_size = len(img_byte_arr.getvalue())

        return img_byte_arr, img_size
    else:
        logger.error(f'이미지 다운 및 압축 실패, 상태 코드 : {response.status_code}')
        return None
