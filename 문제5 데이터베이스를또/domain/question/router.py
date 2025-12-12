# domain/question/router.py
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Question

router = APIRouter(prefix='/question', tags=['question'])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get('', response_model=List[Dict])
def list_questions(db: Session = Depends(get_db)) -> List[Dict]:
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


@router.post('', response_model=Dict)
def create_question(payload: Dict, db: Session = Depends(get_db)) -> Dict:
    subject = str(payload.get('subject') or '').strip()
    content = str(payload.get('content') or '').strip()
    if not subject or not content:
        raise HTTPException(status_code=400, detail='subject 와 content 는 비어 있을 수 없습니다.')

    q = Question(subject=subject, content=content, create_date=datetime.utcnow())
    db.add(q)
    db.commit()
    db.refresh(q)
    return {
        'id': q.id,
        'subject': q.subject,
        'content': q.content,
        'create_date': q.create_date.isoformat(),
    }


@router.get('/{qid}', response_model=Dict)
def get_question(qid: int, db: Session = Depends(get_db)) -> Dict:
    q = db.query(Question).filter(Question.id == qid).first()
    if not q:
        raise HTTPException(status_code=404, detail='존재하지 않는 질문입니다.')
    return {
        'id': q.id,
        'subject': q.subject,
        'content': q.content,
        'create_date': q.create_date.isoformat(),
    }
