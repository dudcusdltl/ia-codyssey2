# schemas.py
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class QuestionRead(BaseModel):
    id: int
    subject: str
    content: str
    create_date: datetime

    class Config:
        orm_mode = True  # False 로 바꿔 실험해 보세요.
