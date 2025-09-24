# crawling_KBS.py
# -*- coding: utf-8 -*-

"""
KBS 최신 헤드라인 크롤러 + 보너스(날씨)
- 제약: 표준 라이브러리 + requests만 사용
- PEP 8, 문자열은 ' ' 기본, 스네이크 케이스 준수
"""

import argparse
import html
import json
import sys
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import urljoin

import requests


API_URL = 'https://news.kbs.co.kr/api/getNewestList'
BASE_URL = 'https://news.kbs.co.kr'
TIMEOUT = 10

# 제목과 링크에서 시도할 키 후보들 (응답 스키마 변동 대비)
TITLE_KEYS = ('newsTitle', 'title', 'headline', 'subject', 'name')
URL_KEYS = ('link_url', 'url', 'newsUrl', 'article_url', 'path', 'link')


def fetch_json(url: str, timeout: int = TIMEOUT) -> Any:
    """API에서 JSON을 받아 파이썬 객체로 반환한다."""
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept': 'application/json,text/plain,*/*',
        'Accept-Language': 'ko,en;q=0.8'
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        return json.loads(resp.text)


def as_iterable(obj: Any) -> Iterable:
    """
    리스트/튜플이면 그대로, dict면 대표 리스트를 찾아 iterable로 만든다.
    - 스키마가 바뀌어도 최대한 자동으로 따라가도록 설계.
    """
    if isinstance(obj, (list, tuple)):
        return obj
    if isinstance(obj, dict):
        # 흔히 쓰이는 컨테이너 키 후보
        for key in ('list', 'items', 'data', 'result', 'rows', 'news', 'contents'):
            val = obj.get(key)
            if isinstance(val, (list, tuple)):
                return val
        # 값들 중 리스트가 있으면 그걸 반환
        for val in obj.values():
            if isinstance(val, (list, tuple)):
                return val
    return []


def pick_first_str(item: Dict[str, Any], keys: Tuple[str, ...]) -> str:
    """주어진 키 후보들 중 첫 번째로 발견되는 문자열 값을 반환한다."""
    for key in keys:
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            return html.unescape(val.strip())
    return ''


def extract_headlines(payload: Any, limit: int, debug: bool = False) -> List[Tuple[str, str]]:
    """
    API 응답에서 (제목, 절대URL) 리스트를 뽑는다.
    URL이 상대경로면 BASE_URL로 보정한다.
    """
    headlines: List[Tuple[str, str]] = []
    seen = set()

    items = list(as_iterable(payload))
    if debug:
        print(f'[디버그] 최상위 컨테이너에서 항목 {len(items)}개 발견')
        if isinstance(payload, dict):
            print(f'[디버그] 루트 dict 키들: {list(payload.keys())[:15]}')

    for item in items:
        if not isinstance(item, dict):
            continue

        title = pick_first_str(item, TITLE_KEYS)
        link = pick_first_str(item, URL_KEYS)

        if not title and debug:
            # 어떤 키가 실제로 들어있는지 힌트 제공
            sample_keys = list(item.keys())[:10]
            print(f'[디버그] 제목 키 미발견, 아이템 키 예시: {sample_keys}')

        if not title:
            continue

        full_url = urljoin(BASE_URL, link) if link else ''
        key = (title, full_url)

        if title not in seen:
            headlines.append((title, full_url))
            seen.add(title)

        if len(headlines) >= limit:
            break

    return headlines


# -------------------- 보너스: 날씨 --------------------

def get_weather_summary(city: str = 'Seoul', timeout: int = TIMEOUT) -> str:
    """
    wttr.in의 간단 JSON을 이용해 현재 날씨 한 줄 요약을 반환한다.
    - requests만 사용
    """
    url = f'http://wttr.in/{city}?format=j1'
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    curr = data['current_condition'][0]
    temp_c = curr.get('temp_C')
    feels = curr.get('FeelsLikeC')
    humidity = curr.get('humidity')
    desc = ''
    wdesc = curr.get('weatherDesc')
    if isinstance(wdesc, list) and wdesc:
        desc = wdesc[0].get('value', '')

    return f'{city}: {desc}, {temp_c}°C (체감 {feels}°C), 습도 {humidity}%'


# -------------------- 출력/진입점 --------------------

def print_headlines(items: List[Tuple[str, str]]) -> None:
    if not items:
        print('헤드라인을 찾지 못했습니다.')
        return

    print('[KBS 최신 헤드라인]')
    for i, (title, url) in enumerate(items, 1):
        print(f'{i:02d}. {title}')
        if url:
            print(f'    - {url}')


def main() -> None:
    parser = argparse.ArgumentParser(description='KBS 최신 헤드라인 + 날씨')
    parser.add_argument('--limit', type=int, default=15, help='헤드라인 출력 개수 (기본 15)')
    parser.add_argument('--city', type=str, default='Seoul', help='날씨 도시명 (기본 Seoul)')
    parser.add_argument('--debug', action='store_true', help='디버그 정보 출력')
    args = parser.parse_args()

    try:
        payload = fetch_json(API_URL)
    except requests.RequestException as exc:
        print(f'오류: KBS API 요청 실패 - {exc}')
        sys.exit(1)

    headlines = extract_headlines(payload, limit=args.limit, debug=args.debug)
    print_headlines(headlines)

    # 보너스: 현재 날씨
    try:
        print('\n[보너스] 현재 날씨')
        print(' - ' + get_weather_summary(args.city))
    except Exception as exc:
        print(f'날씨 정보를 가져오지 못했습니다: {exc}')


if __name__ == '__main__':
    main()
