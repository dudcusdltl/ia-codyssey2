#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sendmail.py - SMTP bulk mailer (stdlib only)
- Python 3.x
- stdlib only: smtplib, ssl, email, csv, argparse, getpass, mimetypes
- HTML body (with plain-text fallback), attachments, CSV targets
- Modes: 'each' (recommended) or 'bulk' (with optional --bcc)
- Placeholders: {name} supported in --subject/--body/--html/--html-file content (only in --mode each)
"""
import argparse
import csv
import getpass
import mimetypes
import os
import smtplib
import socket
import ssl
import sys
from typing import List, Optional, Tuple
from email.message import EmailMessage
from email.utils import formatdate, make_msgid


DEFAULT_SMTP_HOST = 'smtp.gmail.com'
DEFAULT_SMTP_PORT = 587
ENV_USER = 'GMAIL_USER'
ENV_APP_PASSWORD = 'GMAIL_APP_PASSWORD'


def read_targets(csv_path: str) -> List[Tuple[str, str]]:
    """
    CSV에서 '이름, 이메일' 컬럼을 읽어 (이름, 이메일) 목록을 반환한다.
    UTF-8 BOM을 고려하여 utf-8-sig로 연다.
    """
    targets: List[Tuple[str, str]] = []
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f'CSV 파일을 찾을 수 없습니다: {csv_path}')

    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError('CSV 헤더가 없습니다. "이름,이메일" 형식을 확인하세요.')

        # 공백 제거한 키 매핑
        field_map = { (k or '').strip(): k for k in reader.fieldnames }
        name_key = field_map.get('이름') or field_map.get('name') or field_map.get('Name')
        email_key = field_map.get('이메일') or field_map.get('email') or field_map.get('Email')

        if not name_key or not email_key:
            raise ValueError('CSV 헤더에 "이름"과 "이메일" 컬럼이 필요합니다.')

        for row in reader:
            raw_name = (row.get(name_key) or '').strip()
            raw_email = (row.get(email_key) or '').strip()
            if not raw_email:
                continue
            targets.append((raw_name, raw_email))

    if not targets:
        raise ValueError('CSV에서 유효한 대상 이메일을 찾지 못했습니다.')

    return targets


def apply_name_placeholder(s: Optional[str], name: str) -> Optional[str]:
    """
    {name} 플레이스홀더를 단순 치환한다. s가 None 이면 None 반환.
    """
    if s is None:
        return None
    return s.replace('{name}', name)


def build_message(sender: str,
                  to_header_addrs: List[str],
                  subject: str,
                  text_body: Optional[str],
                  html_body: Optional[str],
                  attachments: Optional[List[str]] = None,
                  bcc_addrs: Optional[List[str]] = None) -> EmailMessage:
    """
    EmailMessage를 구성한다. HTML 본문과 첨부를 지원한다.
    """
    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = ', '.join(to_header_addrs) if to_header_addrs else sender
    if bcc_addrs:
        msg['Bcc'] = ', '.join(bcc_addrs)
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid()

    # 본문 구성: text fallback -> html alternative
    safe_text = text_body if text_body is not None else 'This is an HTML email. Please use an HTML-capable client.'
    msg.set_content(safe_text)
    if html_body is not None:
        msg.add_alternative(html_body, subtype='html')

    # 첨부
    if attachments:
        for path in attachments:
            if not path:
                continue
            if not os.path.isfile(path):
                raise FileNotFoundError(f'첨부 파일을 찾을 수 없습니다: {path}')
            ctype, encoding = mimetypes.guess_type(path)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            filename = os.path.basename(path)
            with open(path, 'rb') as f:
                data = f.read()
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

    return msg


def send_mail(host: str,
              port: int,
              username: str,
              password: str,
              message: EmailMessage,
              use_ssl: bool = False,
              debug: bool = False) -> None:
    """
    SMTP 서버에 접속하여 메일을 전송한다.
    """
    context = ssl.create_default_context()

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host=host, port=port, context=context, timeout=30) as server:
                if debug:
                    server.set_debuglevel(1)
                server.login(user=username, password=password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host=host, port=port, timeout=30) as server:
                if debug:
                    server.set_debuglevel(1)
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(user=username, password=password)
                server.send_message(message)
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError('인증 실패: 계정/비밀번호(또는 앱 비밀번호)를 확인하세요.') from e
    except smtplib.SMTPConnectError as e:
        raise RuntimeError('SMTP 서버에 연결하지 못했습니다. 호스트/포트 또는 방화벽 설정을 확인하세요.') from e
    except smtplib.SMTPRecipientsRefused as e:
        raise RuntimeError(f'수신자가 거부되었습니다: {e.recipients}') from e
    except smtplib.SMTPSenderRefused as e:
        raise RuntimeError(f'발신자가 거부되었습니다: {e.sender}') from e
    except smtplib.SMTPException as e:
        raise RuntimeError(f'SMTP 오류가 발생했습니다: {e}') from e
    except (socket.gaierror, TimeoutError) as e:
        raise RuntimeError('네트워크 오류가 발생했습니다. DNS/네트워크 연결을 확인하세요.') from e
    except OSError as e:
        raise RuntimeError(f'시스템 오류가 발생했습니다: {e}') from e


def parse_args() -> argparse.Namespace:
    """
    명령행 인자를 파싱한다.
    """
    parser = argparse.ArgumentParser(
        description='SMTP를 사용해 CSV 대상자에게 HTML 메일을 전송합니다 (표준 라이브러리만 사용).'
    )
    parser.add_argument('--host', default=DEFAULT_SMTP_HOST, help='SMTP 호스트 (기본: smtp.gmail.com)')
    parser.add_argument('--port', type=int, default=DEFAULT_SMTP_PORT, help='SMTP 포트 (기본: 587)')
    parser.add_argument('--ssl', action='store_true', help='SSL 직결 사용 (포트 465 권장)')
    parser.add_argument('--debug', action='store_true', help='SMTP 디버그 출력')

    parser.add_argument('--from', dest='from_addr', required=True, help='발신자 이메일 주소')
    parser.add_argument('--user', dest='username', default=None, help='SMTP 로그인 계정(미지정 시 발신자 사용)')

    parser.add_argument('--subject', required=True, help='메일 제목 (각 수신자 이름 치환 가능: {name})')
    parser.add_argument('--body', default=None, help='텍스트 본문 (선택, {name} 지원)')
    parser.add_argument('--html', default=None, help='HTML 본문 문자열 (선택, {name} 지원)')
    parser.add_argument('--html-file', dest='html_file', default=None, help='HTML 파일 경로 (선택, {name} 지원)')

    parser.add_argument('--csv', dest='csv_path', default='mail_target_list.csv',
                        help='수신자 CSV 경로 (기본: mail_target_list.csv)')

    parser.add_argument('--attach', nargs='*', default=[], help='첨부 파일 경로(복수 지정 가능)')

    parser.add_argument('--mode', choices=['each', 'bulk'], default='each',
                        help='발송 모드: each(개별 발송, 추천) / bulk(일괄 발송)')
    parser.add_argument('--bcc', action='store_true',
                        help='bulk 모드에서 수신자를 Bcc로 숨깁니다.')

    return parser.parse_args()


def load_html_content(args: argparse.Namespace) -> Optional[str]:
    """
    --html 또는 --html-file 로부터 HTML 문자열을 반환한다.
    둘 다 제공되면 --html 가 우선한다.
    """
    if args.html is not None:
        return args.html
    if args.html_file is not None:
        if not os.path.isfile(args.html_file):
            raise FileNotFoundError(f'HTML 파일을 찾을 수 없습니다: {args.html_file}')
        with open(args.html_file, 'r', encoding='utf-8') as f:
            return f.read()
    return None


def main() -> None:
    """
    엔트리 포인트.
    """
    args = parse_args()

    sender = args.from_addr.strip()
    username = (args.username or os.getenv(ENV_USER) or sender).strip()
    app_password = os.getenv(ENV_APP_PASSWORD)
    if not app_password:
        prompt = f'[{username}] 계정의 SMTP 비밀번호(또는 앱 비밀번호)를 입력하세요: '
        app_password = getpass.getpass(prompt=prompt)

    try:
        targets = read_targets(args.csv_path)
    except Exception as e:
        print(f'오류(CSV): {e}', file=sys.stderr)
        sys.exit(1)

    try:
        html_body_raw = load_html_content(args)
    except Exception as e:
        print(f'오류(HTML 로드): {e}', file=sys.stderr)
        sys.exit(1)

    if args.body is None and html_body_raw is None:
        print('오류: --body 또는 --html/--html-file 중 하나는 지정해야 합니다.', file=sys.stderr)
        sys.exit(1)

    attachments = args.attach or []

    if args.mode == 'bulk':
        recipients = [email for _, email in targets]
        to_header_addrs = recipients if not args.bcc else [sender]
        bcc_addrs = recipients if args.bcc else None

        msg = build_message(
            sender=sender,
            to_header_addrs=to_header_addrs,
            subject=args.subject,
            text_body=args.body,
            html_body=html_body_raw,
            attachments=attachments,
            bcc_addrs=bcc_addrs,
        )
        try:
            send_mail(
                host=args.host,
                port=args.port,
                username=username,
                password=app_password,
                message=msg,
                use_ssl=args.ssl or args.port == 465,
                debug=args.debug,
            )
            print(f'메일이 성공적으로 전송되었습니다. (bulk, 대상 {len(recipients)}명)')
        except Exception as e:
            print(f'전송 실패(bulk): {e}', file=sys.stderr)
            sys.exit(1)
        return

    ok = 0
    fail = 0
    for name, email_addr in targets:
        subject = apply_name_placeholder(args.subject, name)
        text_body = apply_name_placeholder(args.body, name) if args.body is not None else None
        html_body = apply_name_placeholder(html_body_raw, name) if html_body_raw is not None else None

        try:
            msg = build_message(
                sender=sender,
                to_header_addrs=[email_addr],
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                attachments=attachments,
                bcc_addrs=None,
            )
        except Exception as e:
            print(f'오류(메시지 구성: {email_addr}): {e}', file=sys.stderr)
            fail += 1
            continue

        try:
            send_mail(
                host=args.host,
                port=args.port,
                username=username,
                password=app_password,
                message=msg,
                use_ssl=args.ssl or args.port == 465,
                debug=args.debug,
            )
            ok += 1
            print(f'전송 성공: {email_addr}')
        except Exception as e:
            fail += 1
            print(f'전송 실패({email_addr}): {e}', file=sys.stderr)

    print(f'요약: 성공 {ok}건, 실패 {fail}건, 총 {ok + fail}건 처리됨.')
    if ok == 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
