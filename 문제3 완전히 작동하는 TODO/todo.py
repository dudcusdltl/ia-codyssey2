# todo.py
from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from model import TodoItem

# -----------------------------
# 전역 리스트 (요구사항)
# -----------------------------
todo_list: List[Dict[str, Any]] = []

# CSV 저장소 경로 (DB 금지 조건 → CSV 사용)
CSV_PATH = 'todo_store.csv'

# -----------------------------
# CSV 유틸
# -----------------------------
def ensure_csv_header() -> None:
    """CSV 파일이 없으면 헤더 포함하여 생성한다."""
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['ts', 'json'])
            writer.writeheader()


def load_from_csv() -> None:
    """CSV 파일에서 데이터를 읽어 todo_list 에 적재한다."""
    ensure_csv_header()
    todo_list.clear()
    with open(CSV_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                data = json.loads(row.get('json', '{}'))
                if isinstance(data, dict):
                    todo_list.append(data)
            except json.JSONDecodeError:
                # 손상된 라인은 무시
                continue


def append_to_csv(item: Dict[str, Any]) -> None:
    """단일 항목을 CSV 파일에 append 한다."""
    ensure_csv_header()
    with open(CSV_PATH, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['ts', 'json'])
        writer.writerow({
            'ts': datetime.now().isoformat(timespec='seconds'),
            'json': json.dumps(item, ensure_ascii=False),
        })


def rewrite_all_csv() -> None:
    """todo_list 전체를 기준으로 CSV 파일을 통째로 다시 쓴다."""
    ensure_csv_header()
    with open(CSV_PATH, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['ts', 'json'])
        writer.writeheader()
        for item in todo_list:
            writer.writerow({
                'ts': datetime.now().isoformat(timespec='seconds'),
                'json': json.dumps(item, ensure_ascii=False),
            })

# -----------------------------
# 헬퍼
# -----------------------------
def find_index_by_id(todo_id: int) -> Optional[int]:
    for idx, item in enumerate(todo_list):
        if item.get('_id') == todo_id:
            return idx
    return None

# -----------------------------
# FastAPI / Router (요구사항)
# -----------------------------
router = APIRouter()


@router.post('/add_todo')
async def add_todo(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    todo_list 에 새로운 Dict 항목을 추가한다. (POST)
    - 입출력 Dict 타입 (요구사항)
    - 보너스(이전 단계): 빈 Dict 입력 시 경고
    """
    if not payload:
        raise HTTPException(status_code=400, detail='요청 본문이 비어 있습니다. 최소 1개 이상의 키-값을 전달하세요.')

    if '_id' not in payload:
        payload['_id'] = int(datetime.now().timestamp())
    if '_created_at' not in payload:
        payload['_created_at'] = datetime.now().isoformat(timespec='seconds')

    todo_list.append(payload)
    append_to_csv(payload)
    return {'result': 'ok', 'added': payload}


@router.get('/retrieve_todo')
async def retrieve_todo() -> Dict[str, Any]:
    """현재 todo_list 를 Dict 형태로 감싸서 반환한다. (GET)"""
    return {'todo_list': todo_list}


@router.get('/todo/{todo_id}')
async def get_single_todo(todo_id: int) -> Dict[str, Any]:
    """
    개별 조회 (GET)
    경로 매개변수로 _id를 받아 단일 항목 반환.
    """
    idx = find_index_by_id(todo_id)
    if idx is None:
        raise HTTPException(status_code=404, detail='해당 ID의 항목을 찾을 수 없습니다.')
    return {'todo': todo_list[idx]}


@router.put('/todo/{todo_id}')
async def update_todo(todo_id: int, patch: TodoItem) -> Dict[str, Any]:
    """
    수정 (PUT)
    경로 매개변수로 _id 지정, body는 TodoItem (Optional 필드 → 부분 수정 허용)
    """
    idx = find_index_by_id(todo_id)
    if idx is None:
        raise HTTPException(status_code=404, detail='해당 ID의 항목을 찾을 수 없습니다.')

    original = todo_list[idx].copy()
    updates = {k: v for k, v in patch.model_dump().items() if v is not None}

    if not updates:
        # 빈 업데이트 방지
        raise HTTPException(status_code=400, detail='수정할 값이 없습니다. 최소 1개 이상의 필드를 전달하세요.')

    # 예약 메타키 보호
    updates.pop('_id', None)
    updates.pop('_created_at', None)

    todo_list[idx].update(updates)
    todo_list[idx]['_updated_at'] = datetime.now().isoformat(timespec='seconds')

    rewrite_all_csv()
    return {'result': 'ok', 'before': original, 'after': todo_list[idx]}


@router.delete('/todo/{todo_id}')
async def delete_single_todo(todo_id: int) -> Dict[str, Any]:
    """
    삭제 (DELETE)
    경로 매개변수로 _id 지정하여 삭제.
    """
    idx = find_index_by_id(todo_id)
    if idx is None:
        raise HTTPException(status_code=404, detail='해당 ID의 항목을 찾을 수 없습니다.')

    removed = todo_list.pop(idx)
    rewrite_all_csv()
    return {'result': 'ok', 'deleted': removed}


def create_app() -> FastAPI:
    app = FastAPI(title='Simple TODO with FastAPI & CSV (CRUD)')
    @app.on_event('startup')
    async def _startup() -> None:
        load_from_csv()

    app.include_router(router)
    return app


app = create_app()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('todo:app', host='0.0.0.0', port=8000, reload=False)
