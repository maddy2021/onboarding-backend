from app.crud.base import CRUDBase
from app.models.designations import Designations
from app.schemas.designations import DesignationsCreate, DesignationsUpdate


class CRUDDesignations(CRUDBase[Designations, DesignationsCreate, DesignationsUpdate]):
    ...


designations = CRUDDesignations(Designations)
