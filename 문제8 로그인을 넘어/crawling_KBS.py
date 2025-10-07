#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
crawling_KBS.py

- 목표
  1) 네이버(https://www.naver.com) 로그인 전/후 콘텐츠 차이 비교
  2) 로그인 상태에서만 접근 가능한 영역 시도 및 결과 확인
  3) (보너스) 네이버 메일(IMAP)에서 받은편지함 제목 목록 출력

- 제약 준수
  * Python 3.x
  * 표준 라이브러리 + requests 만 사용
  * PEP 8 스타일, 문자열은 ' ' 기본
  * 함수/클래스 네이밍 컨벤션 준수

- 사용법(요약)
  $ python crawling_KBS.py

  실행 중 안내에 따라:
   - '쿠키 문자열' 입력(선택): 브라우저에서 로그인 후 DevTools의 'Request Headers'의 'Cookie:' 값 전체를 붙여넣기
   - (보너스) 메일 제목 수집을 원하면 네이버 메일(IMAP) 계정/앱비밀번호 입력
"""

import sys
import re
import imaplib
import getpass
import email
from email.header import decode_header
from html.parser import HTMLParser
from typing import List, Set, Tuple, Dict, Optional

try:
    import requests
except ImportError:
    print('requests 모듈이 필요합니다. 표준 저장소에서 설치 후 다시 실행하세요.')
    sys.exit(1)


NAVER_HOME = 'https://www.naver.com'
NAVER_MAIL_WEB = 'https://mail.naver.com/'
DEFAULT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}


class AnchorParser(HTMLParser):
    """
    매우 단순한 <a> 태그 텍스트 수집기.
    - 사이트 구조 변화에 덜 민감하도록 '보이는 텍스트'만 모아 비교.
    """
    def __init__(self) -> None:
        super().__init__()
        self._in_a = False
        self._buf: List[str] = []
        self.texts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag.lower() == 'a':
            self._in_a = True
            self._buf.clear()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == 'a' and self._in_a:
            text = ''.join(self._buf).strip()
            text = re.sub(r'\s+', ' ', text)
            if text:
                self.texts.append(text)
            self._in_a = False
            self._buf.clear()

    def handle_data(self, data: str) -> None:
        if self._in_a:
            self._buf.append(data)


def parse_cookie_string(cookie_str: str) -> Dict[str, str]:
    """
    'a=1; b=2; ...' 형태의 Cookie 헤더 문자열을 dict로 변환.
    """
    jar: Dict[str, str] = {}
    for part in cookie_str.split(';'):
        part = part.strip()
        if not part:
            continue
        if '=' in part:
            k, v = part.split('=', 1)
            jar[k.strip()] = v.strip()
    return jar


def fetch_html(session: requests.Session, url: str) -> str:
    """
    단순 HTML GET.
    """
    resp = session.get(url, headers=DEFAULT_HEADERS, timeout=15)
    resp.raise_for_status()
    # 일부 리소스는 압축/인코딩 포함 -> requests가 적절히 decode
    return resp.text


def extract_anchor_texts(html: str) -> Set[str]:
    """
    <a> 텍스트 집합 추출.
    """
    parser = AnchorParser()
    parser.feed(html)
    return set(t for t in parser.texts if t)


def compare_logged_in_out(anon_html: str, login_html: str) -> Tuple[Set[str], Set[str]]:
    """
    로그인 전 대비 로그인 후에만 보이는 앵커 텍스트, 반대 케이스를 반환.
    """
    anon = extract_anchor_texts(anon_html)
    login = extract_anchor_texts(login_html)
    only_when_logged_in = login - anon
    only_when_logged_out = anon - login
    return only_when_logged_in, only_when_logged_out


def looks_logged_in(html: str) -> bool:
    """
    매우 단순한 휴리스틱:
    - 로그인 상태면 보통 상단에 '로그아웃' / '메일'의 개인화 영역이 나타남.
    - 사이트 변경 가능성을 고려하여 키워드 여러 개로 확인.
    """
    keywords = ['로그아웃', '내정보', '메일', 'MY', '네이버페이']
    score = sum(1 for k in keywords if k in html)
    return score >= 2


def probe_login_only_area(session: requests.Session) -> str:
    """
    '로그인 필요' 영역 접근 시도 결과를 설명 문자열로 반환.
    - 예시 URL: 네이버 메일 웹
    """
    try:
        r = session.get(NAVER_MAIL_WEB, headers=DEFAULT_HEADERS, timeout=15, allow_redirects=True)
        final_url = r.url
        text = r.text
        # 로그인 안 되어 있으면 보통 로그인 페이지로 리다이렉트 또는 '로그인' 안내가 보임
        if '로그인' in text and '아이디' in text and '비밀번호' in text:
            return '메일 웹 접근: 로그인 페이지로 유도됨(로그인 필요).'
        if '메일' in text or '받은편지함' in text:
            return '메일 웹 접근: 콘텐츠 일부가 보임(로그인 상태로 추정).'
        # 최종 URL로도 판별
        if 'nid.naver.com' in final_url:
            return '메일 웹 접근: nid 로그인 도메인으로 리다이렉트됨(로그인 필요).'
        return f'메일 웹 접근: 상태 불명(HTTP {r.status_code}, 최종 URL: {final_url}).'
    except Exception as e:
        return f'메일 웹 접근 중 예외 발생: {e}'


def decode_mime_words(s: bytes) -> str:
    """
    메일 제목의 MIME 인코딩 디코딩.
    """
    parts = decode_header(s)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            try:
                out.append(text.decode(enc or 'utf-8', errors='replace'))
            except Exception:
                out.append(text.decode('utf-8', errors='replace'))
        else:
            out.append(text)
    return ''.join(out)


def list_naver_mail_subjects(user: str, app_password: str, limit: int = 20) -> List[str]:
    """
    (보너스) 네이버 메일 IMAP을 사용해 받은편지함 제목 N개 수집.
    - 표준 라이브러리만 사용(imaplib, email)
    - IMAP 사용을 위해 네이버에서 '앱 비밀번호' 발급 필요
    """
    subjects: List[str] = []
    M = imaplib.IMAP4_SSL('imap.naver.com', 993)
    try:
        # 로그인
        code, msg = M.login(user, app_password)
        if code != 'OK':
            raise RuntimeError('IMAP 로그인 실패')
        # 받은편지함 선택
        M.select('INBOX')
        # 최신 메일부터 limit개
        code, data = M.search(None, 'ALL')
        if code != 'OK' or not data or not data[0]:
            return subjects
        ids = data[0].split()
        ids = ids[-limit:]
        for mid in reversed(ids):
            code, msg = M.fetch(mid, '(BODY.PEEK[HEADER.FIELDS (SUBJECT)])')
            if code != 'OK' or not msg:
                continue
            # msg는 튜플들의 리스트
            raw = b''
            for part in msg:
                if isinstance(part, tuple):
                    raw += part[1] or b''
            # 파싱
            try:
                msgobj = email.message_from_bytes(raw)
                raw_subj = msgobj.get('Subject', '')
                if isinstance(raw_subj, str):
                    subjects.append(raw_subj)
                else:
                    subjects.append(decode_mime_words(raw_subj))
            except Exception:
                subjects.append('(제목 파싱 실패)')
        return subjects
    finally:
        try:
            M.logout()
        except Exception:
            pass


def main() -> None:
    print('=== 네이버 로그인 전/후 비교 & 메일 제목 수집(보너스) ===\n')

    # 1) 세션 준비(비로그인)
    anon = requests.Session()

    # 2) (선택) 로그인 쿠키 문자열 입력 받아 로그인 세션 구성
    print('[선택] 이미 브라우저에서 로그인한 상태라면, 개발자도구(Network)에서')
    print('       "Request Headers"의 Cookie: 전체 문자열을 복사해 여기에 붙여넣으세요.')
    print('       빈 줄로 두면 비로그인 상태로 진행합니다.')
    cookie_str = input('\n쿠키 문자열(없으면 Enter): ').strip()

    login_sess = requests.Session()
    if cookie_str:
        login_sess.cookies.update(parse_cookie_string(cookie_str))
    # 공통 헤더
    login_sess.headers.update(DEFAULT_HEADERS)
    anon.headers.update(DEFAULT_HEADERS)

    print('\n[1] 네이버 메인 HTML 가져오는 중(비로그인)…')
    anon_html = fetch_html(anon, NAVER_HOME)
    print('    완료.')

    print('[2] 네이버 메인 HTML 가져오는 중(로그인 세션)…')
    login_html = fetch_html(login_sess, NAVER_HOME)
    print('    완료.')

    # 3) 로그인 전/후 차이 비교(앵커 텍스트 기반 간단 비교)
    only_in_login, only_in_anon = compare_logged_in_out(anon_html, login_html)

    print('\n[결과] 로그인 판단(휴리스틱): ', '로그인 상태 추정' if looks_logged_in(login_html) else '비로그인 상태 추정')
    print('\n[로그인 상태에서만 보이는 링크 텍스트 후보 Top 20]')
    for i, t in enumerate(sorted(only_in_login, key=len, reverse=True)[:20], 1):
        print(f'{i:2d}. {t}')

    print('\n[로그인하지 않을 때만 보이는 링크 텍스트 후보 Top 10]')
    for i, t in enumerate(sorted(only_in_anon, key=len, reverse=True)[:10], 1):
        print(f'{i:2d}. {t}')

    # 4) 로그인 필요 영역 접근 시도(설명 출력)
    print('\n[3] 로그인 필요 페이지 접근 시도:')
    print(' - 대상: 네이버 메일 웹')
    result = probe_login_only_area(login_sess)
    print('   ->', result)

    # 5) 보너스 과제: IMAP으로 받은편지함 제목 가져오기
    print('\n[보너스] 네이버 메일 제목 수집(IMAP, 표준 라이브러리만 사용)')
    print('   * 네이버 계정에서 IMAP 사용 및 앱 비밀번호가 필요합니다.')
    use_mail = input('   진행할까요? (y/N): ').strip().lower() == 'y'
    if use_mail:
        user = input('   네이버 메일 아이디(전체 주소 또는 @ 이전 아이디): ').strip()
        if '@' not in user:
            user = user + '@naver.com'
        app_pw = getpass.getpass('   앱 비밀번호(입력 숨김): ')
        try:
            subjects = list_naver_mail_subjects(user, app_pw, limit=20)
            if not subjects:
                print('   (가져온 제목이 없습니다. 권한/함/필터를 확인하세요.)')
            else:
                print('\n   [최신 받은편지함 제목 Top 20]')
                for i, s in enumerate(subjects, 1):
                    print(f'   {i:2d}. {s}')
        except Exception as e:
            print(f'   메일 수집 중 오류: {e}')

    print('\n끝.')


if __name__ == '__main__':
    main()
