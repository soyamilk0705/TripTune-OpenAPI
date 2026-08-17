import requests
import re
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
    파라미터로 전달된 여행지 이미지 url에서 이미지를 다운로드 한 후 압축한다.

    [Parameter]
    image_url: open api 에서 제공하는 여행지 이미지 url
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
        logger.error(f"이미지 다운 및 압축 실패, 상태 코드 : {response.status_code}")
        return None


def clean_use_time(use_time: str | None):
    if not use_time:
        return use_time

    original = use_time

    # --------------------------------
    # 1. 개행/단락 기호(¶)를 모두 <br>로 일차 통일
    # --------------------------------
    use_time = re.sub(
        r'(?:<br\s*/?>|¶|\r?\n)',
        '<br>',
        use_time,
        flags=re.IGNORECASE
    )

    # --------------------------------
    # 2. ※가 나오면 앞에 <br> 추가
    # --------------------------------
    use_time = re.sub(
        r'(?<!^)[ \t]*(※)',
        r'<br>\1',
        use_time
    )

    # --------------------------------
    # 3. [문자] 항목이 나오면 앞에 <br> 추가
    # --------------------------------
    use_time = re.sub(
        r'(?<!^)[ \t]*(\[)',
        r'<br>\1',
        use_time
    )

    # --------------------------------
    # 4. [대항목]- 소항목 패턴 처리
    # --------------------------------
    use_time = re.sub(
        r'\]\s*-\s*',
        r']<br>- ',
        use_time
    )

    # --------------------------------
    # 5. 시간/숫자/문자 뒤에 - 소항목 패턴 처리
    # --------------------------------
    use_time = re.sub(
        r'(\d{1,2}:\d{2})\s*-\s*(?=[^\d\s])',
        r'\1<br>- ',
        use_time
    )

    # -------------------------------------------------------------
    # 6. 위 과정에서 발생한 중복 <br> (예: <br><br>, <br> <br> 등)
    #    및 주변 공백을 하나의 <br>로 일괄 합치기
    # -------------------------------------------------------------
    use_time = re.sub(
        r'(?:\s*<br\s*/?>\s*)+',
        '<br>',
        use_time,
        flags=re.IGNORECASE
    )

    # 앞뒤 불필요한 <br> 정리
    use_time = re.sub(
        r'^(?:<br>)+|(?:<br>)+$',
        '',
        use_time
    )

    if original != use_time:
        logger.info(f"[EDIT] 이용시간 데이터 정제 | {original} → {use_time}")

    return use_time
