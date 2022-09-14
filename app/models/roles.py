from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Roles(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(56), nullable=False)
    allow_all = Column(Boolean,default=False)
    user = relationship("User",secondary="user_roles",back_populates="roles")
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
