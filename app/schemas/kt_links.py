from pydantic import BaseModel
from typing import List, Optional


class KtLinksBase(BaseModel):
    display_name: str
    kt_url: str
    project_id: int

# Properties to receive via API on creation
class KtLinksCreate(KtLinksBase):
    ...

# Properties to receive via API on update
class KtLinksUpdate(KtLinksBase):
    id: int

class KtLinksDelete(BaseModel):
    id: int


class KtLinksInDBBase(KtLinksBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True

# Additional properties to return via API
class KtLinks(KtLinksInDBBase):
    pass
