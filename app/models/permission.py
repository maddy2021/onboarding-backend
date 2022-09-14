from sqlalchemy import Column, ForeignKey, Integer, String
from app.db.base_class import Base


class Permission(Base):
    id = Column(Integer, primary_key=True)
    code = Column(String(56), nullable=False, unique=True)
    display_name = Column(String(56),nullable= False)
    created_by = Column(
        Integer,
        ForeignKey('user.id'),nullable=True,
        # no need to add index=True, all FKs have indexes
    )
    modified_by = Column(
        Integer,
        ForeignKey('user.id'),nullable=True,
        # no need to add index=True, all FKs have indexes
    )
