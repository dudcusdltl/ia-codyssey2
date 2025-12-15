# main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import engine, Base
from domain.question.question_router import router as question_router

app = FastAPI(title='Mars Board – Questions (Final)')

Base.metadata.create_all(bind=engine)
app.include_router(question_router)
app.mount('/frontend', StaticFiles(directory='frontend', html=True), name='frontend')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)
