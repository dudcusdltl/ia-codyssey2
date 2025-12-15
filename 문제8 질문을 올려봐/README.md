# Mars Board – Questions (Final)

FastAPI + SQLite + SQLAlchemy + contextlib DI 기반 질문 목록/등록 예제입니다.

## 엔드포인트
- GET /api/question
- POST /api/question  (JSON: {"subject": "...", "content": "..."})
- 프론트엔드: /frontend

## 실행
pip install fastapi uvicorn sqlalchemy pydantic
uvicorn main:app --reload

## 확인
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/frontend
