#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sendmail.py — Gmail SMTP 발송 스크립트 (표준 라이브러리만 사용)
- Python 3.x
- 외부 패키지 불필요 (smtplib, ssl, email.*, getpass, argparse 등 표준 라이브러리만 사용)
- PEP 8 스타일 및 문자열은 기본적으로 단일 인용부호(' ') 사용
- 예외 처리 포함
- 첨부파일 전송(보너스) 지원
""" 
import argparse
import getpass
import mimetypes
import os
import smtplib
import socket
import ssl
import sys
from email.message import EmailMessage
from email.utils import formatdate, make_msgid


DEFAULT_SMTP_HOST = 'smtp.gmail.com'
DEFAULT_SMTP_PORT = 587  # STARTTLS 권장 (대안: 465 SSL)
ENV_USER = 'GMAIL_USER'
ENV_APP_PASSWORD = 'GMAIL_APP_PASSWORD'  # 2단계 인증 사용 시 앱 비밀번호 보관에 권장


def build_message(sender: str, recipients: list[str], subject: str, body: str,
                  attachments: list[str] | None = None) -> EmailMessage:
    """
    이메일 메시지를 구성한다. 첨부파일을 지원한다.
    :param sender: 발신자 이메일
    :param recipients: 수신자 이메일 리스트
    :param subject: 제목
    :param body: 본문(plain text)
    :param attachments: 첨부 파일 경로 리스트
    :return: EmailMessage 객체
    """
    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid()
    msg.set_content(body)

    if attachments:
        for path in attachments:
            path = path.strip()
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


def send_mail(host: str, port: int, username: str, password: str, message: EmailMessage,
              use_ssl: bool = False, debug: bool = False) -> None:
    """
    SMTP 서버에 접속하여 메일을 전송한다.
    :param host: SMTP 호스트
    :param port: 포트 (STARTTLS: 587, SSL: 465)
    :param username: 로그인 계정(일반적으로 발신자와 동일)
    :param password: 비밀번호(또는 앱 비밀번호)
    :param message: EmailMessage
    :param use_ssl: SSL 직접 연결 여부 (True 면 465 권장)
    :param debug: smtplib 디버그 출력 여부
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
        raise RuntimeError('인증 실패: Gmail 계정/비밀번호(앱 비밀번호)를 확인하세요. '
                           '2단계 인증 사용 시 앱 비밀번호가 필요합니다.') from e
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
        description='Gmail SMTP를 사용하여 이메일을 전송합니다 (표준 라이브러리만 사용).'
    )
    parser.add_argument('--host', default=DEFAULT_SMTP_HOST, help='SMTP 호스트명 (기본: smtp.gmail.com)')
    parser.add_argument('--port', type=int, default=DEFAULT_SMTP_PORT, help='SMTP 포트 (기본: 587)')
    parser.add_argument('--ssl', action='store_true', help='SSL 직접 연결 사용 (포트 465 권장)')
    parser.add_argument('--debug', action='store_true', help='SMTP 디버그 출력 활성화')

    parser.add_argument('--from', dest='from_addr', required=True, help='발신자 이메일 주소')
    parser.add_argument('--to', dest='to_addrs', required=True,
                        help='수신자 이메일 주소 (쉼표로 여러 명 지정 가능)')
    parser.add_argument('--subject', required=True, help='메일 제목')
    parser.add_argument('--body', required=True, help='메일 본문(텍스트)')
    parser.add_argument('--attach', nargs='*', default=[], help='첨부 파일 경로(복수 지정 가능)')
    parser.add_argument('--user', dest='username', default=None,
                        help='SMTP 로그인 계정(미지정 시 발신자 주소 사용)')

    return parser.parse_args()


def main() -> None:
    """
    엔트리 포인트. 인자 파싱, 자격 증명 수집, 메시지 생성 및 전송을 수행한다.
    """
    args = parse_args()

    sender = args.from_addr.strip()
    recipients = [x.strip() for x in args.to_addrs.split(',') if x.strip()]
    if not recipients:
        print('오류: 수신자(--to)가 올바르지 않습니다.', file=sys.stderr)
        sys.exit(1)

    username = (args.username or os.getenv(ENV_USER) or sender).strip()

    app_password = os.getenv(ENV_APP_PASSWORD)
    if not app_password:
        prompt = f'[{username}] 계정의 Gmail 앱 비밀번호를 입력하세요: '
        app_password = getpass.getpass(prompt=prompt)

    try:
        message = build_message(
            sender=sender,
            recipients=recipients,
            subject=args.subject,
            body=args.body,
            attachments=args.attach,
        )
    except FileNotFoundError as e:
        print(f'오류: {e}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # 예기치 못한 메시지 구성 오류
        print(f'오류(메시지 구성): {e}', file=sys.stderr)
        sys.exit(1)

    try:
        send_mail(
            host=args.host,
            port=args.port,
            username=username,
            password=app_password,
            message=message,
            use_ssl=args.ssl or args.port == 465,
            debug=args.debug,
        )
        print('메일이 성공적으로 전송되었습니다.')
    except Exception as e:
        print(f'전송 실패: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
