from typing import Optional, List
from pydantic import BaseModel


class ProjectBase(BaseModel):
    project_code: str
    display_name: str
    project_details: Optional[str] = None

class ProjectNameOnly(BaseModel):
    display_name: str

# Properties to receive via API on creation
class ProjectCreate(ProjectBase):
    ...

# Properties to receive via API on update
class ProjectUpdate(ProjectBase):
    id: int

class ProjectDelete(BaseModel):
    id: int


class ProjectInDBBase(ProjectBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

# Additional properties to return via API
class Projects(ProjectInDBBase):
    ...
    from app.schemas.tools import Tools
    tools: List[Tools] = []

class ProjectToolsAssignment(BaseModel):
    tool_id: int  

class ProjectTools(BaseModel):
    from app.schemas.tools import ToolsInDBBase
    tools: List[ToolsInDBBase] = []

    class Config:
        orm_mode = True  

# class SubscriberUser(BaseModel):
#     from app.schemas.user import UserInDBBase
#     user: List[UserInDBBase] = []
#     class Config:
#         orm_mode = True

# class SubscriberUserBase(SubscriberInDBBase):
#     from app.schemas.user import UserInDBBase
#     user: List[UserInDBBase] = []
#     class Config:
#         orm_mode = True

# class SubscriberCommodity(BaseModel):
#     from app.schemas.commodity import CommodityInDBBase
#     commodity: List[CommodityInDBBase] = []
#     class Config:
#         orm_mode = True

# class SubscriberSpread(BaseModel):
#     from app.schemas.spread import SpreadInDBBase
#     Spread: List[SpreadInDBBase] = []
#     class Config:
#         orm_mode = True

# class SubscriberLookahead(BaseModel):
#     from app.schemas.lookahead import LookaheadInDBBase
#     lookahead: List[LookaheadInDBBase] = []
#     class Config:
#         orm_mode = True

# class SubscriberCommodityBase(SubscriberInDBBase):
#     from app.schemas.commodity import CommodityInDBBase
#     commodity: List[CommodityInDBBase] = []
#     class Config:
#         orm_mode = True

# class SubscriberSpreadBase(SubscriberInDBBase):
#     from app.schemas.spread import SpreadInDBBase
#     spread: List[SpreadInDBBase] = []
#     class Config:
#         orm_mode = True

# class SubscriberLookaheadBase(SubscriberInDBBase):
#     from app.schemas.lookahead import LookaheadBase
#     lookahead: List[LookaheadInDBBase] = []
#     class Config:
#         orm_mode = True

