# models.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from database import Base


class Question(Base):
    __tablename__ = 'question'

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(200), nullable=False, index=True)
    content = Column(String, nullable=False)
    create_date = Column(DateTime, nullable=False, default=datetime.utcnow)
