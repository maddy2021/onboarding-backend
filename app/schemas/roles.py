from pydantic import BaseModel
from typing import List, Optional

class RolesBase(BaseModel):
    name: str
    allow_all: bool = False
    status: int = 1

class RolesNameOnly(BaseModel):
    name: str
    # allow_all: bool = False
    # status: int = 1


# Properties to receive via API on creation
class RoleCreate(RolesBase):
    name: str
    allow_all: bool = False
    status: int = 1

# Properties to receive via API on update
class RoleUpdate(RolesBase):
    name: Optional[str] = None
    id: int

class RoleDelete(BaseModel):
    id: int


class RoleInDBBase(RolesBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

# Additional properties to return via API
class Role(RoleInDBBase):
    pass 
