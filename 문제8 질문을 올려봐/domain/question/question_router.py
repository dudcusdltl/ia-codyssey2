# domain/question/question_router.py
from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db_dep
from models import Question
from schemas import QuestionCreate, QuestionRead

router = APIRouter(prefix='/api/question', tags=['question'])


@router.get('', response_model=List[QuestionRead])
def question_list(db: Session = Depends(get_db_dep)) -> list[Question]:
    items = db.query(Question).order_by(Question.id.desc()).all()
    return items


@router.post('', response_model=QuestionRead, status_code=201)
def question_create(data: QuestionCreate, db: Session = Depends(get_db_dep)) -> Question:
    q = Question(
        subject=data.subject,
        content=data.content,
        create_date=datetime.utcnow(),
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q
