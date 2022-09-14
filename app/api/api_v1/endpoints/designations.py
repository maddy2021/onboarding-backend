from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Any, List
from app import crud
from app.api import deps
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.schemas.designations import Designations, DesignationsCreate, DesignationsDelete, DesignationsUpdate

router = APIRouter()

@router.post("/", status_code=201, response_model=Designations, 
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.ADD.name))
# ]
)
def create_designations(
    *,request:Request, designation_in: DesignationsCreate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Create a new role in the database.
    """
    # user_in.expiry_date = parser.parse(user_in.expiry_date)
    designation = crud.designations.create(db=db, obj_in=designation_in)

    return designation

@router.get("/getById/{designation_id}", status_code=200, response_model=Designations, 
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.VIEW.name))
# ]
)
def fetch_roles(
    *,
    designation_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch a single designation by ID
    """
    result = crud.designations.get(db=db, id=designation_id)
    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        return {}
    return result

@router.get("/getall", status_code=200, response_model=List[Designations], 
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.VIEW.name))
# ]
)
def fetch_all_designation(
    *,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch all roles
    """
    designations = crud.designations.get_multi(db=db)
    if not designations:
        return []
    return designations

@router.post("/update", status_code=201, response_model=Designations, 
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.EDIT.name))
# ]
)
def update_designation(
    *, request:Request,designation_in: DesignationsUpdate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Update a new role in the database.
    provide fields which need to be updtaed and id is must needed
    """
    result = crud.designations.get(db=db, id=designation_in.id)
    designation = crud.designations.update(db=db,db_obj=result ,obj_in=designation_in)
    
    return designation

@router.post("/delete", status_code=201, response_model=Designations, 
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.EDIT.name))
# ]
)
def delete_designation(
    *, request:Request,designation_in: DesignationsDelete, db: Session = Depends(deps.get_db)
) -> dict:
    """
    delete a new role in the database.
    provide fields which need to be updtaed and id is must needed
    """
    # result = crud.roles.get(db=db, id=role_in.id)
    deleted_designation = crud.designations.remove(db=db,id=designation_in.id)
    
    return deleted_designation
