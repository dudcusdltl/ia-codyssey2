# main.py
from __future__ import annotations

from fastapi import FastAPI

from database import engine
from models import Base
from domain.question.router import router as question_router

app = FastAPI(title='Mars Board (FastAPI + SQLite + SQLAlchemy)')

# 앱 시작 전에 마이그레이션이 적용되어 있다면 아래 두 줄은 필요 없습니다.
# 학습 편의를 위해, 마이그레이션 없이도 개발 첫 실행에 테이블이 없으면 생성되도록 둡니다.
Base.metadata.create_all(bind=engine)

app.include_router(question_router)

# uvicorn main:app --reload
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)
