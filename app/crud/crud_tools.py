from app.crud.base import CRUDBase
from app.models.tools import Tools
from app.schemas.tools import ToolsCreate, ToolsUpdate


class CRUDTools(CRUDBase[Tools, ToolsCreate, ToolsUpdate]):
    ...


tools = CRUDTools(Tools)
