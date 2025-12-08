# client.py
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request


BASE = 'http://127.0.0.1:8000'


def pretty(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def post_add(payload: dict) -> dict:
    url = f'{BASE}/add_todo'
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))


def get_all() -> dict:
    url = f'{BASE}/retrieve_todo'
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode('utf-8'))


def get_one(todo_id: int) -> dict:
    url = f'{BASE}/todo/{todo_id}'
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode('utf-8'))


def put_update(todo_id: int, patch: dict) -> dict:
    url = f'{BASE}/todo/{todo_id}'
    data = json.dumps(patch).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='PUT')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))


def delete_one(todo_id: int) -> dict:
    url = f'{BASE}/todo/{todo_id}'
    req = urllib.request.Request(url, method='DELETE')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))


def main() -> None:
    print('간단 TODO 클라이언트 (Enter 로 기본값 적용)')
    print('서버가 127.0.0.1:8000 에서 실행 중이어야 합니다.')

    while True:
        print('\n[메뉴] 1)추가  2)전체조회  3)개별조회  4)수정  5)삭제  0)종료')
        choice = input('선택: ').strip() or '2'
        try:
            if choice == '1':
                title = input('title: ').strip() or '무제'
                owner = input('owner: ').strip() or 'anonymous'
                done_in = input('done(true/false, 기본 false): ').strip().lower()
                done = True if done_in == 'true' else False
                res = post_add({'title': title, 'owner': owner, 'done': done})
                print(pretty(res))

            elif choice == '2':
                res = get_all()
                print(pretty(res))

            elif choice == '3':
                todo_id = int(input('todo_id: ').strip())
                res = get_one(todo_id)
                print(pretty(res))

            elif choice == '4':
                todo_id = int(input('todo_id: ').strip())
                print('빈 값은 무시됩니다(부분 수정).')
                title = input('title(옵션): ').strip()
                owner = input('owner(옵션): ').strip()
                note = input('note(옵션): ').strip()
                done_in = input('done(true/false, 옵션): ').strip().lower()

                patch = {}
                if title:
                    patch['title'] = title
                if owner:
                    patch['owner'] = owner
                if note:
                    patch['note'] = note
                if done_in in ('true', 'false'):
                    patch['done'] = True if done_in == 'true' else False

                res = put_update(todo_id, patch)
                print(pretty(res))

            elif choice == '5':
                todo_id = int(input('todo_id: ').strip())
                res = delete_one(todo_id)
                print(pretty(res))

            elif choice == '0':
                print('종료합니다.')
                break

            else:
                print('올바른 메뉴를 선택하세요.')
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode('utf-8')
                print(f'HTTP {e.code}: {detail}')
            except Exception:
                print(f'HTTP {e.code}')
        except Exception as e:
            print(f'오류: {e}')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
