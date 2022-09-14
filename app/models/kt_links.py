from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float
from app.db.base_class import Base


class KtLinks(Base):
    id = Column(Integer, primary_key=True)
    # code = Column(String(56), nullable=False, unique=True)
    display_name = Column(String(56),nullable= False)
    kt_url = Column(String(50000),nullable= False)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'),nullable= True)
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

