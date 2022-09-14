from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Any, List
from app import crud
from app.api import deps
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.schemas.kt_links import KtLinks, KtLinksCreate, KtLinksDelete, KtLinksUpdate
from app.schemas.role_permission import RolePermission
from app.schemas.role_permission import RolePermissionIn

from app.schemas.roles import RoleCreate, Role, RoleDelete, RoleUpdate
from app.schemas.user import User
from app.util.user_util import get_current_user

router = APIRouter()

@router.post("/", status_code=201, response_model=dict, 
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.ADD.name))
# ]
)
def create_kt_links(
    *,request:Request, kt_links_in: List[KtLinksCreate], db: Session = Depends(deps.get_db)
) -> dict:
    """
    Create a new Kt links in the database.
    """
    current_user: User = get_current_user(request)
    created_by = current_user.id 
    # user_in.expiry_date = parser.parse(user_in.expiry_date)
    kt_links = crud.kt_links.create(db=db,obj_in=kt_links_in,created_by=created_by)
    
    return {"created": True}

@router.get("/getall", status_code=200, response_model=List[KtLinks], 
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.VIEW.name))
# ]
)
def fetch_project_kt_links(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = 0
) -> Any:
    """
    Fetch all kt links by project
    """
    kt_links = crud.kt_links.get_kt_docs_by_prj_id(db=db,prj_id=project_id)
    if not kt_links:
        return []
    return kt_links

@router.post("/update", status_code=201, response_model=KtLinks, 
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.EDIT.name))
# ]
)
def update_kt_links(
    *, request:Request,role_kt_link_in: KtLinksUpdate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Update a new role in the database.
    provide fields which need to be updtaed and id is must needed
    """
    result = crud.kt_links.get(db=db, id=role_kt_link_in.id)
    kt_link = crud.kt_links.update(db=db,db_obj=result ,obj_in=role_kt_link_in)
    
    return kt_link

@router.post("/delete", status_code=201, response_model=KtLinks, 
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.EDIT.name))
# ]
)
def delete_kt_links(
    *, request:Request,kt_links_in: KtLinksDelete, db: Session = Depends(deps.get_db)
) -> dict:
    """
    delete a new role in the database.
    provide fields which need to be updtaed and id is must needed
    """
    # result = crud.roles.get(db=db, id=role_in.id)
    deleted_kt_link = crud.kt_links.remove(db=db,id=kt_links_in.id)
    
    return deleted_kt_link
