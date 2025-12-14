# database.py
from __future__ import annotations

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

SQLALCHEMY_DATABASE_URL = 'sqlite:///./app.db'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={'check_same_thread': False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


@contextmanager
def get_db() -> Session:
    """
    contextlib.contextmanager 를 사용한 DB 세션 컨텍스트.
    호출부에서 with get_db() as db: 형태로 사용하면, 사용 후 자동 close 됩니다.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_dep():
    """
    FastAPI Depends() 에서 사용할 어댑터.
    위의 get_db() 는 contextmanager 객체를 반환하므로, Depends에 바로 전달할 수 없습니다.
    따라서 이 래퍼에서 with 블록으로 진입해 세션을 yield 합니다.
    """
    with get_db() as db:
        yield db
