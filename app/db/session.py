from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI
    # required for sqlite
    # connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# engine_1 = create_engine(
#     # settings.SQLALCHEMY_CRUDE_PALM_OIL_URI
#     # required for sqlite
#     # connect_args={"check_same_thread": False},
# )
# SessionLocal_1 = sessionmaker(autocommit=False, autoflush=False, bind=engine_1)
