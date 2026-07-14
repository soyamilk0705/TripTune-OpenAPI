import sys
import urllib.parse
import requests
import xml.etree.ElementTree as ET
from utils.log_handler import setup_logger


logger = setup_logger()


def fetch_page_api_items(url : str, params : dict, page_no):
    """
    get_json_data 함수를 통해 api 요청해 요청 결과에 item 만 추출해서 리스트에 저장한다.
    요청 페이지 번호의 데이터를 가져온다.

    *api 요청 결과는 {'response':{'header':{...}, 'body':{'items':'item':[]}}} 으로 구성되어 있다.

    [Parameter]
    url: open api 요청 url
    params: open api 요청 파라미터
    page_no: 페이지 번호

    [Return]
    items : 요청 결과 중 item 값만 담은 리스트
    """
    # 첫 페이지 요청
    params['pageNo'] = page_no
    content = get_json_data(url, params)

    body = content['response']['body']

    if body['totalCount'] == 0:
        return []

    return body['items']['item']


def fetch_first_page_api_items(url : str, params : dict):
    """
    get_json_data 함수를 통해 api 요청해 요청 결과에 item 만 추출해서 리스트에 저장한다.
    pageNo = 1 로 설정해 최대 10개의 데이터만 요청하도록 한다.

    *api 요청 결과는 {'response':{'header':{...}, 'body':{'items':'item':[]}}} 으로 구성되어 있다.

    [Parameter]
    url: open api 요청 url
    params: open api 요청 파라미터

    [Return]
    items : 요청 결과 중 item 값만 담은 리스트
    """
    params['pageNo'] = 1

    content = get_json_data(url, params)
    body = content['response']['body']

    if body['totalCount'] == 0:
        return []
    
    return body['items']['item']


def fetch_total_api_items(url: str, params: dict):
    """
    get_json_data 함수를 통해 api 요청해 요청 결과에 item 만 추출해서 리스트에 저장한다.
    total_count 로 총 페이지 수(pageNo) 를 계산해 반복문에 이용한다.

    *api 요청 결과는 {'response':{'header':{...}, 'body':{'items':'item':[]}}} 으로 구성되어 있다.

    [Parameter]
    url: open api 요청 url
    params: open api 요청 파라미터

    [Return]
    items : 요청 결과 중 item 값만 담은 리스트
    """
    items = []

    # 첫 페이지 요청
    content = get_json_data(url, params)

    body = content['response']['body']
    total_count = body['totalCount']

    if total_count == 0:
        return items

    items.extend(body['items']['item'])

    total_pages = (total_count - 1) // params['numOfRows'] + 1

    # 2페이지부터 요청
    for page_no in range(2, total_pages + 1):
        params['pageNo'] = page_no

        content = get_json_data(url, params)

        items.extend(
            content['response']['body']['items']['item']
        )

    return items


def get_json_data(url : str, params : dict):
    """
    api 요청 후 json으로 변환한다.
    요청 시 특수문자로 인한 오류를 방지하기 위해 파라미터 값들을 인코딩한다.

    * open api 요청 결과가 XML 인 경우 에러 페이지이기 때문에 그에 따른 try-except를 추가하였다.


    [Parameter]
    url: open api 요청 url
    params: open api 요청 파라미터
    """
    encoding_params = urllib.parse.urlencode(params, safe='#\':()+=%,')

    response = requests.get(url, params=encoding_params)
    content_type = response.headers.get('Content-Type')

    if response.status_code == 200:
        if 'application/json' in content_type:
            try:
                data = response.json()
                print(data)

                if 'response' in data and 'body' in data['response']:
                    return data
                elif 'resultMsg' in data and 'resultCode' in data:
                    logger.error(f'get_json_data() - 에러 코드 : {data["resultCode"]}, 에러 메시지: {data["resultMsg"]}')
                    sys.exit(1)
                else:
                    logger.error('get_json_data() - 예상치 못한 응답 구조 발생: {data}')
                    sys.exit(1)

            except ValueError as e:
                logger.error(f'get_json_data() - JSON 파싱 오류: {e}')
                sys.exit(1)

        elif 'application/xml' in content_type or 'text/xml' in content_type:
            try:
                root = ET.fromstring(response.text)
                logger.error(f'get_json_data() - 에러 코드 : {root.find(".//returnReasonCode").text}\n에러 메시지 : {root.find(".//returnAuthMsg").text}')
                sys.exit(1)

            except ET.ParseError as e:
                logger.error('get_json_data() - XML 파싱 오류 : {e}')
                sys.exit(1)
        else:
            logger.error(f'get_json_data() - 알 수 없는 컨텐츠 타입 : {content_type}')
            sys.exit(1)
    else:
        logger.error(f'get_json_data() - 요청 실패: 상태코드 {response.status_code}\n컨텐츠 타입 : {content_type}')
        sys.exit(1)


