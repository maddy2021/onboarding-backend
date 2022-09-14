from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Any, List
from app import crud
from app.api import deps
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.schemas.role_permission import RolePermission
from app.schemas.role_permission import RolePermissionIn

from app.schemas.roles import RoleCreate, Role, RoleDelete, RoleUpdate

router = APIRouter()

@router.post("/", status_code=201, response_model=Role, dependencies=[
    Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.ADD.name))
])
def create_roles(
    *,request:Request, role_in: RoleCreate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Create a new role in the database.
    """
    # user_in.expiry_date = parser.parse(user_in.expiry_date)
    role = crud.roles.create(db=db, obj_in=role_in)

    return role

@router.get("/getById/{role_id}", status_code=200, response_model=Role, dependencies=[
    Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.VIEW.name))
])
def fetch_roles(
    *,
    role_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch a single role by ID
    """
    result = crud.roles.get(db=db, id=role_id)
    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        return {}
    return result

@router.get("/getall", status_code=200, response_model=List[Role], dependencies=[
    Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.VIEW.name))
])
def fetch_all_roles(
    *,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch all roles
    """
    roles = crud.roles.get_multi(db=db)
    if not roles:
        return []
    return roles

@router.post("/update", status_code=201, response_model=Role, 
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.EDIT.name))
# ]
)
def update_role(
    *, request:Request,role_in: RoleUpdate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Update a new role in the database.
    provide fields which need to be updtaed and id is must needed
    """
    result = crud.roles.get(db=db, id=role_in.id)
    role = crud.roles.update(db=db,db_obj=result ,obj_in=role_in)
    
    return role

@router.post("/delete", status_code=201, response_model=Role, 
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.EDIT.name))
# ]
)
def delete_role(
    *, request:Request,role_in: RoleDelete, db: Session = Depends(deps.get_db)
) -> dict:
    """
    delete a new role in the database.
    provide fields which need to be updtaed and id is must needed
    """
    # result = crud.roles.get(db=db, id=role_in.id)
    deleted_role = crud.roles.remove(db=db,id=role_in.id)
    
    return deleted_role

@router.post("/{role_id}/permission", status_code=201, response_model=List[RolePermission],dependencies=[
    Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.ADD.name))
])
def assign_permission(
    *, role_id: int,permission_in: RolePermissionIn, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Assign permission to role
    """
    roles = crud.role_permission.assign_permission(db=db, obj_in=permission_in, role_id = role_id)
    return roles

@router.get("/{role_id}/permission", status_code=200, response_model=List[RolePermission],dependencies=[
    Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.VIEW.name))
])
def fetch_assigned_permission(
    *,
    role_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch assigned permission for role
    """
    result = crud.role_permission.get_assigned_permissions(db=db, role_id=role_id)
    return result
