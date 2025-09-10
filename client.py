#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import sys


def recv_loop(sock: socket.socket) -> None:
    buf = b''
    while True:
        try:
            chunk = sock.recv(4096)
        except OSError:
            break
        if not chunk:
            break
        buf += chunk
        while b'\n' in buf:
            line, buf = buf.split(b'\n', 1)
            try:
                print(line.decode('utf-8', errors='replace'))
            except UnicodeDecodeError:
                pass


def main() -> None:
    # 기본값을 둬서 F5만 눌러도 돌아감 (로컬 과제용)
    host = '127.0.0.1'
    port = 5000
    nickname = 'user'

    if len(sys.argv) == 4:
        host = sys.argv[1]
        port = int(sys.argv[2])
        nickname = sys.argv[3]
    elif len(sys.argv) not in (1, 4):
        print('사용법: python client.py <host> <port> <nickname>')
        sys.exit(1)

    if not nickname.strip():
        print('닉네임은 비어있을 수 없습니다.')
        sys.exit(1)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
    except OSError as exc:
        print(f'[ERROR] 서버 접속 실패: {exc}')
        sys.exit(1)

    # 접속 즉시 닉네임 1줄 전송
    sock.sendall((nickname + '\n').encode('utf-8'))

    t = threading.Thread(target=recv_loop, args=(sock,), daemon=True)
    t.start()

    try:
        while True:
            try:
                line = input()
            except EOFError:
                line = '/종료'
            text = (line or '').rstrip('\n')
            try:
                sock.sendall((text + '\n').encode('utf-8'))
            except OSError:
                print('[INFO] 서버 연결 종료')
                break
            if text == '/종료':
                break
    finally:
        try:
            sock.close()
        except OSError:
            pass


if __name__ == '__main__':
    main()
