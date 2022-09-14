from app.crud.base import CRUDBase
from app.models.kt_links import KtLinks
from app.schemas.kt_links import KtLinksCreate, KtLinksUpdate
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session


class CRUDKtLinks(CRUDBase[KtLinks, KtLinksCreate, KtLinksUpdate]):
    def create(self, db: Session, *, obj_in: List[KtLinksCreate], created_by=None) -> KtLinks:
        # print(db_obj.last_login_date)
        objects = []
        for kt_link_obj in obj_in:
            db_item = self.model(**kt_link_obj.dict())
            objects.append(db_item)
        db.bulk_save_objects(objects)
        db.commit()
        # db.refresh(objects)
        return objects

    def get_kt_docs_by_prj_id(self, db: Session, prj_id: int) -> Optional[KtLinks]:
        return db.query(KtLinks).filter(KtLinks.project_id == prj_id).all()


kt_links = CRUDKtLinks(KtLinks)


