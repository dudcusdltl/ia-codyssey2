#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading

clients = {}           # sock -> nickname
clients_lock = threading.Lock()


def broadcast(text: str, exclude=None) -> None:
    data = (text + '\n').encode('utf-8', errors='replace')
    with clients_lock:
        targets = [s for s in clients.keys() if s is not exclude]
    for s in targets:
        try:
            s.sendall(data)
        except OSError:
            # 보내다 실패하면 정리
            remove_client(s)


def remove_client(sock: socket.socket) -> None:
    nickname = None
    with clients_lock:
        nickname = clients.pop(sock, None)
    try:
        sock.close()
    except OSError:
        pass
    if nickname:
        broadcast(f'[SYSTEM] [{nickname}] 님이 퇴장하셨습니다.')


def handle_client(sock: socket.socket) -> None:
    try:
        nickname = recv_line(sock)
        if nickname is None or not nickname.strip():
            sock.sendall('[SYSTEM] 닉네임이 비었습니다.\n'.encode('utf-8'))
            sock.close()
            return
        nickname = nickname.strip()

        with clients_lock:
            clients[sock] = nickname

        sock.sendall('[SYSTEM] 연결됨. "/종료" 종료, "/w 닉 메시지" 귓속말.\n'.encode('utf-8'))
        broadcast(f'[SYSTEM] [{nickname}] 님이 입장하셨습니다.', exclude=None)

        while True:
            line = recv_line(sock)
            if line is None:
                break
            text = line.strip()
            if not text:
                continue

            if text == '/종료':
                break

            if text.startswith('/w '):
                # /w target message
                parts = text.split(' ', 2)
                if len(parts) < 3:
                    sock.sendall('[SYSTEM] 사용법: /w 닉네임 메시지\n'.encode('utf-8'))
                    continue
                _, target_name, content = parts
                send_whisper(nickname, target_name, content, sock)
                continue

            broadcast(f'{nickname}> {text}')
    finally:
        remove_client(sock)


def send_whisper(sender: str, target_name: str, content: str, sender_sock: socket.socket) -> None:
    target_sock = None
    with clients_lock:
        for s, name in clients.items():
            if name == target_name:
                target_sock = s
                break
    if target_sock is None:
        sender_sock.sendall(f'[SYSTEM] 대상 [{target_name}] 없음.\n'.encode('utf-8'))
        return
    for s, msg in ((target_sock, f'(귓속말) {sender}> {content}'),
                   (sender_sock, f'(귓속말 보냄) {target_name}에게> {content}')):
        try:
            s.sendall((msg + '\n').encode('utf-8'))
        except OSError:
            pass


def recv_line(sock: socket.socket) -> str | None:
    buf = b''
    while True:
        if b'\n' in buf:
            line, buf = buf.split(b'\n', 1)
            # 남은 건 버려도 단순 과제엔 충분
            try:
                return line.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                return None
        try:
            chunk = sock.recv(4096)
        except OSError:
            return None
        if not chunk:
            return None
        buf += chunk


def main() -> None:
    import sys
    # 인자 없이도 바로 돌아가게 기본값 제공 (로컬 테스트 초간단)
    host = '127.0.0.1'
    port = 5000
    if len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
    elif len(sys.argv) not in (1, 3):
        print('사용법: python server.py <host> <port>')
        sys.exit(1)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(50)
    print(f'[INFO] listening on {host}:{port}')

    try:
        while True:
            c, a = srv.accept()
            t = threading.Thread(target=handle_client, args=(c,), daemon=True)
            t.start()
    finally:
        srv.close()


if __name__ == '__main__':
    main()
