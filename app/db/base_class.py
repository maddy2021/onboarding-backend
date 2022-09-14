import typing as t

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from app.db.session import engine
from sqlalchemy import Column,DateTime
from sqlalchemy.types import SmallInteger
from sqlalchemy.sql import func
from datetime import date, datetime, timedelta


class_registry: t.Dict = {}

@as_declarative(class_registry=class_registry,bind=engine)
class BaseDefault:
    id: t.Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


@as_declarative(class_registry=class_registry,bind=engine)
class Base:
    id: t.Any
    __name__: str
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    modified_date = Column(DateTime(timezone=True), onupdate=func.now())
    status = Column(SmallInteger , nullable=False, default=1)
    
    

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
