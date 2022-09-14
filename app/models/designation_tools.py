from sqlalchemy import Column, ForeignKey, Integer
from app.db.base_class import Base


class DesignationTools(Base):
    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer,
        ForeignKey('projects.id',ondelete='CASCADE'),nullable=True,
    )
    designation_id= Column(
        Integer,
        ForeignKey('designations.id',ondelete='CASCADE'),nullable=True,
    )
    tool_id=Column(
        Integer,
        ForeignKey('tools.id',ondelete='CASCADE'),nullable=True,
    )
