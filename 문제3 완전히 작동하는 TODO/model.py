# model.py
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class TodoItem(BaseModel):
    """
    수정(UPDATE) 시 사용할 모델.
    PUT을 사용하지만 부분 수정이 가능하도록 모든 필드를 Optional로 둔다.
    """
    title: Optional[str] = None
    owner: Optional[str] = None
    done: Optional[bool] = None
    note: Optional[str] = None
