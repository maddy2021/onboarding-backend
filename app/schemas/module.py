from pydantic import BaseModel
from typing import Optional


class ModuleBase(BaseModel):
    code: str
    display_name: str
    parent_id : Optional[int] = None
    sequence: float
    is_header: bool = False


# Properties to receive via API on creation
class ModuleCreate(ModuleBase):
    ...

# Properties to receive via API on update
class ModuleUpdate(ModuleBase):
    id: int


class ModuleInDBBase(ModuleBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

# Additional properties to return via API
class Module(ModuleInDBBase):
    pass
