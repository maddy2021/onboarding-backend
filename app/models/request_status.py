from sqlalchemy import Column, ForeignKey, Integer, ARRAY, String
from app.db.base_class import Base


class RequestStatus(Base):
    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer,nullable=True,
    )
    project_name = Column(String(100),nullable=True)
    employee_email=Column(String(100),nullable=True)
    employee_first_name = Column(String(100),nullable=True)
    employee_id = Column(Integer,nullable=True)

    manager_name=Column(String(15),nullable=False)
    config_managers=Column(
        ARRAY(String(100)),nullable=True,
    )
    tools=Column(ARRAY(String(100)),nullable=True)
    req_status = Column(String(15), nullable=False)
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
