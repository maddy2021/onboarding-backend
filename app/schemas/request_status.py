from pydantic import BaseModel, EmailStr
from typing import List, Optional

class RequestStatusBase(BaseModel):
    project_id: int
    # user_id: int
    project_name: str
    employee_email: EmailStr
    employee_first_name: str
    employee_id: str
    manager_name: str
    config_managers: List[str]
    tools: List[str]
    req_status: str


# Properties to receive via API on creation
class RequestStatusCreate(RequestStatusBase):
    pass
    # project_id: int
    # user_id: int
    # manager_id: int
    # config_manager_id: List[int]
    # tools: List[int]

# Properties to receive via API on update
class RequestStatusUpdate(RequestStatusBase):
    id: int

# class RoleDelete(BaseModel):
#     id: int


class RequestStatusInDBBase(RequestStatusBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

# Additional properties to return via API
class RequestStatus(RequestStatusInDBBase):
    pass 
