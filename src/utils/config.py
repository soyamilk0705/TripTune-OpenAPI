import os
from dotenv import load_dotenv

BASE_URL = 'http://apis.data.go.kr/B551011/KorService2'
NUM_OF_ROWS = 10
MOBILE_OS = 'ETC'
MOBILE_APP = 'TripTune'
RESPONSE_TYPE = 'json'


def get_secret_key():
    load_dotenv()

    # tour api
    secret_key = os.getenv('SECRET_KEY')

    if not secret_key:
        print('tour api secret key 환경 변수 불러오기 실패')
        return None

    return secret_key



def build_params():
    secret_key = get_secret_key()
    
    return {
        'serviceKey': secret_key,
        'numOfRows': NUM_OF_ROWS,
        'pageNo': 1,
        'MobileOS': MOBILE_OS,
        'MobileApp': MOBILE_APP,
        '_type': RESPONSE_TYPE
    }

def build_detail_params():
    secret_key = get_secret_key()

    return {
        'serviceKey': secret_key,
        'numOfRows': NUM_OF_ROWS,
        'pageNo': 1,
        'MobileOS': MOBILE_OS,
        'MobileApp': MOBILE_APP,
        '_type': RESPONSE_TYPE
    }



def build_image_params():
    secret_key = get_secret_key()

    return {
        'serviceKey': secret_key,
        'numOfRows': NUM_OF_ROWS,
        'pageNo': 1,
        'MobileOS': MOBILE_OS,
        'MobileApp': MOBILE_APP,
        '_type': RESPONSE_TYPE,
        'imageYN': 'Y'
    }