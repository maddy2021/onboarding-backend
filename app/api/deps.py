from typing import Generator

from app.db.session import SessionLocal

def get_db() -> Generator:
    db = SessionLocal()
    db.current_user_id = None
    try:
        yield db
    finally:
        db.close()

# def get_db_1() -> Generator:
#     db = SessionLocal_1()
#     db.current_user_id = None
#     try:
#         yield db
#     finally:
#         db.close()
