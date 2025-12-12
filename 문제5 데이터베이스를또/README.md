# Mars Board (FastAPI + SQLite + SQLAlchemy + Alembic)

간단한 게시판 백엔드입니다. 질문(Question) 테이블을 SQLite에 저장하며, SQLAlchemy ORM과 Alembic 마이그레이션을 사용합니다.

## 구조
```
.
├── main.py
├── database.py
├── models.py
├── domain
│   └── question
│       └── router.py
├── alembic
│   ├── env.py
│   └── versions
│       └── 0001_create_question.py
├── alembic.ini
└── frontend
    └── README.md
```

## 요구 패키지
```bash
pip install fastapi uvicorn sqlalchemy alembic
```

## 실행(개발용)
```bash
# 1) 가상환경(선택)
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# 2) 패키지 설치
pip install fastapi uvicorn sqlalchemy alembic

# 3) (처음 학습용) 테이블 자동 생성 옵션으로 바로 실행
uvicorn main:app --reload
# 또는 아래 Alembic 마이그레이션 적용 후 실행
```

## Alembic 사용법
이 리포에는 alembic 초기화와 첫 마이그레이션이 포함되어 있습니다.

### 1) 마이그레이션 적용
```bash
alembic upgrade head
```

### 2) 수정이 생겼다면 새 리비전 생성
모델 수정 후:
```bash
alembic revision -m "your message"
# 생성된 파일에 op.* 를 작성한 뒤
alembic upgrade head
```

> 참고: `alembic.ini` 의 `sqlalchemy.url` 은 `sqlite:///./app.db` 로 설정되어 있습니다.

## API
- 문서: http://127.0.0.1:8000/docs

### 엔드포인트
- `GET /question` : 질문 목록
- `POST /question` : 질문 생성 (JSON: `{{"subject": "...", "content": "..."}}`)
- `GET /question/{id}` : 질문 단건

## SQLite 테이블 확인
```bash
python -c "import sqlite3; conn=sqlite3.connect('app.db'); print(conn.execute('SELECT name FROM sqlite_master WHERE type=\'table\';').fetchall()); conn.close()"
# 또는 DB Browser for SQLite 로 app.db 열어 확인
```

## 스타일
- PEP 8 준수, 문자열은 기본 `' '` 사용.
- `autocommit=False`, `autoflush=False`.
