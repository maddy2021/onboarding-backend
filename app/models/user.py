from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, Table, SmallInteger
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.models.projects import Projects
from app.models.designations import Designations


user_roles = Table('user_roles', Base.metadata,
                   Column('user_id', ForeignKey('user.id'), primary_key=True),
                   Column('role_id', ForeignKey('roles.id'), primary_key=True)
                   )

user_projects = Table('user_projects', Base.metadata,
                   Column('user_id', ForeignKey('user.id'), primary_key=True),
                   Column('project_id', ForeignKey('projects.id'), primary_key=True)
                   )


class User(Base):
    id = Column(Integer, primary_key=True)
    first_name = Column((String(32)), nullable=False)
    last_name = Column((String(32)), nullable=True)
    employee_id = Column(Integer,nullable=False)
    email = Column((String(256)), unique=True, nullable=False)
    email_confirmed = Column(Boolean, nullable=False, default=False)
    password = Column((String()), nullable=True)
    phone = Column((String(15)), nullable=True)
    phone_confirmed = Column(Boolean, nullable=False, default=False)
    # lockout_end = Column(DateTime, nullable=True)
    # lockout_enabled = Column(Boolean, nullable=True, default=False)
    # access_failed_count = Column(Boolean, nullable=False, default=0)
    is_super_admin = Column(Boolean, nullable=False, default=False)
    base_location = Column(String(15),nullable=True)
    status = Column(SmallInteger , nullable=False, default=1)
    # last_login_date = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    projects = relationship("Projects", secondary="user_projects", back_populates="user")
    roles = relationship("Roles", secondary="user_roles", back_populates="user")
    designation_id =  Column(Integer, ForeignKey('designations.id'),nullable= True)

    def toJson(self):
        return {
            "id": self.id,
            "email": self.email,
            "is_super_admin": self.is_super_admin,
            "status": self.status
        }
