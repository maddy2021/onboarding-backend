from pydantic import BaseModel
from typing import List, Optional


class RolePermissionBase(BaseModel):
    permission_id: int
    roles_id: int
    module_id: int 

class PermissionModule(BaseModel):
    module_id: Optional[int]
    permission_id: Optional[int]

class RolePermissionIn(BaseModel):
    Permission: List[PermissionModule]


class PermissionInDBBase(RolePermissionBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

# Additional properties to return via API
class RolePermission(PermissionInDBBase):
    ...
