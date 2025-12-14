# main.py
from __future__ import annotations

from fastapi import FastAPI

from database import engine
from models import Base
from domain.question.question_router import router as question_router

app = FastAPI(title='Mars Board (FastAPI + SQLite + SQLAlchemy)')

# 개발 편의상: 마이그레이션 전이라면 최초 실행 시 테이블 생성
Base.metadata.create_all(bind=engine)

# 신규 라우터 등록
app.include_router(question_router)

# uvicorn main:app --reload
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)
