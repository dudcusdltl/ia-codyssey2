# Mars Board – contextlib 기반 DI + Pydantic 스키마

## 파일
- database.py : contextlib.contextmanager 로 get_db() 제공, Depends용 래퍼 get_db_dep() 포함
- models.py : SQLAlchemy Question 모델
- schemas.py : Pydantic QuestionRead (Config.orm_mode=True)
- domain/question/question_router.py : 목록 API (GET /api/question)
- main.py : 앱/라우터 등록

## 실행
pip install fastapi uvicorn sqlalchemy alembic pydantic
uvicorn main:app --reload

## 확인
- 문서: http://127.0.0.1:8000/docs
- 목록: GET /api/question

## 보너스
schemas.py 의 Config.orm_mode 를 False 로 바꾸고 서버 재실행 →
ORM 객체 그대로 반환 시 검증 오류가 납니다. (dict가 아니므로)
반대로 True 일 때는 ORM 속성을 읽어 직렬화합니다.
