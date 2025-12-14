# domain/question/question_router.py
from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Question

router = APIRouter(prefix='/api/question', tags=['question'])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get('', response_model=List[Dict])
def question_list(db: Session = Depends(get_db)) -> List[Dict]:
    """
    질문 목록을 반환합니다. (GET)
    - SQLite에 저장된 데이터를 SQLAlchemy ORM으로 조회합니다.
    - 응답은 Dict 리스트 형태로 반환합니다.
    """
    items = db.query(Question).order_by(Question.id.desc()).all()
    return [
        {
            'id': q.id,
            'subject': q.subject,
            'content': q.content,
            'create_date': q.create_date.isoformat(),
        }
        for q in items
    ]
