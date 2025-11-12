# 프로젝트 폴더에서
python -m venv .venv
# (Windows) 
.venv\Scripts\activate
# (macOS/Linux)
source .venv/bin/activate

# 필수 패키지 설치 (요구사항 예외: FastAPI, uvicorn만 사용)
pip install fastapi uvicorn



# todo.py
from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, FastAPI, HTTPException, Request

# -----------------------------
# 전역 리스트 (요구사항)
# -----------------------------
todo_list: List[Dict[str, Any]] = []

# CSV 저장소 경로 (DB 사용 금지 조건으로 CSV 사용)
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

# -----------------------------
# FastAPI / Router (요구사항)
# -----------------------------
router = APIRouter()


@router.post('/add_todo')
async def add_todo(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    todo_list 에 새로운 Dict 항목을 추가한다. (POST)
    - 입출력 Dict 타입 (요구사항)
    - 보너스: 빈 Dict 입력 시 경고 반환
    """
    if not payload:
        # 보너스 과제: 빈 dict 경고
        raise HTTPException(status_code=400, detail='요청 본문이 비어 있습니다. 최소 1개 이상의 키-값을 전달하세요.')

    # 편의용 메타 필드(자동 ID/타임스탬프) 추가: 사용자가 보낸 키와 충돌하지 않도록 접두어 사용
    if '_id' not in payload:
        payload['_id'] = int(datetime.now().timestamp())
    if '_created_at' not in payload:
        payload['_created_at'] = datetime.now().isoformat(timespec='seconds')

    todo_list.append(payload)
    append_to_csv(payload)
    return {'result': 'ok', 'added': payload}


@router.get('/retrieve_todo')
async def retrieve_todo() -> Dict[str, Any]:
    """
    현재 todo_list 를 Dict 형태로 감싸서 반환한다. (GET)
    - 입출력 Dict 타입 (요구사항: 리스트를 Dict 로 감싸 전달)
    """
    return {'todo_list': todo_list}


def create_app() -> FastAPI:
    app = FastAPI(title='Simple TODO with FastAPI & CSV')
    # 서버 시작 시 CSV -> 메모리 적재
    @app.on_event('startup')
    async def _startup() -> None:
        load_from_csv()

    app.include_router(router)
    return app


app = create_app()

# uvicorn 으로 실행 (요구사항)
# 예:  uvicorn todo:app --reload
if __name__ == '__main__':
    # 개발 편의를 위해 직접 실행도 지원
    import uvicorn
    uvicorn.run('todo:app', host='0.0.0.0', port=8000, reload=False)
