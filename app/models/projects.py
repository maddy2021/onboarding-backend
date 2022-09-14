from sqlalchemy import Column, ForeignKey, Integer, String, Date, Table, BigInteger
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import date, timedelta
from app.models.tools import Tools
from app.models.kt_links import KtLinks
from app.models.designation_tools import DesignationTools

projects_tools = Table('projects_tools', Base.metadata,
                   Column('project_id', ForeignKey('projects.id'), primary_key=True),
                   Column('tool_id', ForeignKey('tools.id'), primary_key=True)
                   )


class Projects(Base):
    id = Column(Integer, primary_key=True, index=True)
    project_code = Column((String(15)), nullable=False)
    display_name = Column((String(100)),nullable=False)
    project_details = Column((String(6400000)),nullable=True)
    # kt_description = Column((String(10485760)),nullable=True)
    # expiry_date = Column(Date, default=date.today() +
    #                      timedelta(days=90), nullable=True)
    ky_links = relationship("KtLinks",backref='projects', passive_deletes=True)
    designationtools = relationship("DesignationTools", backref="projects")
    user = relationship("User",secondary="user_projects",back_populates="projects")
    tools = relationship("Tools",secondary="projects_tools",back_populates="projects")
    created_by = Column(
        Integer,
        ForeignKey('user.id',use_alter=True), nullable=True,
        # no need to add index=True, all FKs have indexes
    )
    modified_by = Column(
        Integer,
        ForeignKey('user.id',use_alter=True), nullable=True,
        # no need to add index=True, all FKs have indexes
    )
