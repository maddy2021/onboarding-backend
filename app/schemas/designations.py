from pydantic import BaseModel
from typing import List, Optional


class DesignationsBase(BaseModel):
    code: str
    display_name: str

# Properties to receive via API on creation
class DesignationsCreate(DesignationsBase):
    ...

# Properties to receive via API on update
class DesignationsUpdate(DesignationsBase):
    id: int

class DesignationsDelete(BaseModel):
    id: int

class DesignationsInDBBase(DesignationsBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

# Additional properties to return via API
class Designations(DesignationsInDBBase):
    pass
