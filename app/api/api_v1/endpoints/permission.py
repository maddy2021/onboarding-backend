from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Any, List

from app import crud
from app.api import deps
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
# from dateutil import parser

from app.schemas.permission import PermissionCreate, Permission, PermissionUpdate
from app.schemas.user import User
from app.util.user_util import get_current_user

router = APIRouter()

@router.get("/getById/{permission_id}", status_code=200, response_model=Permission,dependencies=[
    Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.VIEW.name))
])
def fetch_permission(
    *,
    permission_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch a single permission by ID
    """
    result = crud.permission.get(db=db, id=permission_id)
    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        return {}
    return result

@router.get("/getall", status_code=200, response_model=List[Permission],dependencies=[
    Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.VIEW.name))
])
def fetch_all_permission(
    *,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch all permission
    """
    permissions = crud.permission.get_multi(db=db)
    if not permissions:
        return {}
    return permissions

@router.post("/update", status_code=201, response_model=Permission,dependencies=[
    Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.EDIT.name))
])
def update_permission(
    *,request:Request, permission_in: PermissionUpdate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Update a new permission in the database.
    provide fields which need to be updtaed and id is must needed
    """
    current_user: User = get_current_user(request)
    modified_by = current_user.id 
    result = crud.permission.get(db=db, id=permission_in.id)
    permission = crud.permission.update(db=db,db_obj=result ,obj_in=permission_in, modified_by=modified_by)    
    return permission

@router.post("/", status_code=201, response_model=Permission,dependencies=[
    Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.ADD.name))
])
def create_permission(
    *,request:Request, role_in: PermissionCreate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Create a new permission in the database.
    """
    current_user: User = get_current_user(request)
    created_by = current_user.id 
    # user_in.expiry_date = parser.parse(user_in.expiry_date)
    role = crud.permission.create(db=db, obj_in=role_in,created_by=created_by)
    return role
