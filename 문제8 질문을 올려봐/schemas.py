# schemas.py
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, constr


class QuestionCreate(BaseModel):
    subject: constr(min_length=1, strip_whitespace=True)  # type: ignore[var-annotated]
    content: constr(min_length=1, strip_whitespace=True)  # type: ignore[var-annotated]


class QuestionRead(BaseModel):
    id: int
    subject: str
    content: str
    create_date: datetime

    class Config:
        orm_mode = True
