from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float
from app.db.base_class import Base


class Module(Base):
    id = Column(Integer, primary_key=True)
    code = Column(String(56), nullable=False, unique=True)
    display_name = Column(String(56),nullable= False)
    parent_id = Column(Integer, ForeignKey('module.id'),nullable= True)
    sequence = Column(Float, nullable= False)
    is_header = Column(Boolean, nullable=False, default=False)
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

