from datetime import datetime
from typing import Any, List, Optional
from xmlrpc.client import boolean
from pydantic import BaseModel, EmailStr, validator
from app.schemas.role_permission import RolePermissionBase


class UserBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    employee_id: int
    email: Optional[EmailStr] = None
    email_confirmed: bool = False
    password: Optional[str] = None
    phone: Optional[str] = None
    phone_confirmed: bool = False
    # lockout_end: Optional[datetime] = None
    # lockout_enabled: bool = False
    # access_failed_count: int = 0
    is_super_admin: bool = False
    base_location: Optional[str] = None
    status: int = 1
    designation_id: Optional[int] = None
    # last_login_date: Optional[datetime] = None

    # @validator("last_login_date")
    # def parse_birthdate(cls, last_login_date):
    #     return datetime.strftime(
    #         last_login_date,
    #         "%Y-%m-%dT%H:%M:%S.%f"
    #     )
class UserDeleted(BaseModel):
    id: int
    employee_id: int
    is_deleted: boolean


class UserCreate(UserBase):
    first_name: str
    last_name: Optional[str] = None
    employee_id: int
    email: EmailStr
    password: Optional[str] = None
    phone: Optional[str] = None
    # lockout_end: Optional[datetime] = None
    status: int = 1
    # last_login_date: Optional[datetime] = None
    base_location: Optional[str] = None
    designation_id: Optional[int] = None

# Properties to receive via API on update
class UserUpdate(UserBase):
    id: int

class UserDelete(BaseModel):
    id: int

# Used to get configuration users object
class ConfigUsers(BaseModel):
    first_name: str
    last_name: str
    employee_id: int
    email: str
    phone: str


class UserInDBBase(UserBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

# Additional properties to return via API
class User(UserInDBBase):
    ...
    from app.schemas.roles import Role
    from app.schemas.projects import Projects
    roles: List[Role] = []
    projects: List[Projects] = []

class UserOnly(UserInDBBase):
    ...

class UserSearchResults(BaseModel):
    results: List[User] = []


class UserRoleAssignment(BaseModel):
    role_id: int

class UserRole(BaseModel):
    from app.schemas.roles import RoleInDBBase
    roles: List[RoleInDBBase] = []

    class Config:
        orm_mode = True  

class UserProjectAssignment(BaseModel):
    project_id: int  

class UserProject(BaseModel):
    from app.schemas.projects import ProjectInDBBase
    projects: List[ProjectInDBBase] = []

    class Config:
        orm_mode = True  

class UserCacheSchema(BaseModel):
    id: int
    email: str
    is_super_admin: bool
    status: int

class AccessRequest(BaseModel):
    id: int
    first_name: str
    last_name: str
    employee_id: int
    email: str
    base_location: str
    projects: List[str]
    configuration_user: List[str]
    project_tools: List[str]
