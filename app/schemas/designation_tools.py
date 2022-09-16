from pydantic import BaseModel
from typing import List, Optional


class DesignationToolsBase(BaseModel):
    project_id: int
    designation_id: int
    tool_id: int 

class DesignationTools(BaseModel):
    project_id: int
    designation_id: Optional[int]
    tool_id: Optional[int]

class DesignationToolsTable(BaseModel):
    designation_name: str
    tools: List[str]


class RolePermissionIn(BaseModel):
    Permission: List[DesignationTools]


class PermissionInDBBase(DesignationToolsBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

# Additional properties to return via API
class RolePermission(PermissionInDBBase):
    ...
