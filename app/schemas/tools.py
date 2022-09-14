from pydantic import BaseModel
from typing import List, Optional


class ToolsBase(BaseModel):
    code: str
    display_name: str
    tool_type: str

# Properties to receive via API on creation
class ToolsCreate(ToolsBase):
    code: str = None
    display_name: str = None
    tool_type: str = None

# Properties to receive via API on update
class ToolsUpdate(ToolsBase):
    id: int

class ToolsDelete(BaseModel):
    id: int


class ToolsInDBBase(ToolsBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

# Additional properties to return via API
class Tools(ToolsInDBBase):
    pass
