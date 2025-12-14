# main.py
from __future__ import annotations

from fastapi import FastAPI
from database import engine, Base
from domain.question.question_router import router as question_router

app = FastAPI(title='Mars Board with contextlib DI')

Base.metadata.create_all(bind=engine)
app.include_router(question_router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)
