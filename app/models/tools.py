from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, Date
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.models.designation_tools import DesignationTools


class Tools(Base):
    id = Column(Integer, primary_key=True)
    code = Column(String(56), nullable=False, unique=True)
    display_name = Column(String(56),nullable= False)
    tool_type = Column(String(10),nullable=False)
    designationtools = relationship("DesignationTools", backref='tools')
    projects = relationship("Projects",secondary="projects_tools",back_populates="tools")
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
