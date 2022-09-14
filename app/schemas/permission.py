from pydantic import BaseModel
from typing import Optional


class PermissionBase(BaseModel):
    code: str
    display_name: str
    # status: int = 1

# Properties to receive via API on creation
class PermissionCreate(PermissionBase):
    code: str
    display_name: str
    # status: int = 1

# Properties to receive via API on update
class PermissionUpdate(PermissionBase):
    id: int


class PermissionInDBBase(PermissionBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

# Additional properties to return via API
class Permission(PermissionInDBBase):
    pass