from app.crud.base import CRUDBase
from app.models.module import Module
from app.schemas.module import ModuleCreate, ModuleUpdate


class CRUDModule(CRUDBase[Module, ModuleCreate, ModuleUpdate]):
    ...


module = CRUDModule(Module)
