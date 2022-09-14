from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Any, List


from app import crud
from app.api import deps
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.schemas.tools import Tools, ToolsCreate, ToolsDelete, ToolsUpdate
from app.models.user import User
# from dateutil import parser

from app.util.user_util import get_current_user

router = APIRouter()

@router.post("/", status_code=201, response_model=Tools,dependencies=[
    # Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.ADD.name))
])
def create_tools(
    *, request: Request,tools_in: ToolsCreate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Create a new tools in the database.
    """
    current_user: User = get_current_user(request)
    created_by = current_user.id 
    # user_in.expiry_date = parser.parse(user_in.expiry_date)
    tools = crud.tools.create(db=db, obj_in=tools_in,created_by=created_by)
    return tools

@router.get("/getall", status_code=200, response_model=List[Tools],dependencies=[
    # Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.VIEW.name))
])
def get_tools(
    *,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch a all tools
    """
    result = crud.tools.get_multi(db=db)
    if not result:
        return []
    return result


@router.post("/update", status_code=201, response_model=Tools,
# dependencies=[
    # Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.EDIT.name))
# ]
)
def update_tool(
    *, request:Request,tools_in: ToolsUpdate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Update a commodity in the database.
    provide fields which need to be updtaed and id is must needed
    """
    current_user: User = get_current_user(request)
    modified_by = current_user.id 
    result = crud.tools.get(db=db, id=tools_in.id)
    tool_data = crud.tools.update(db=db, db_obj=result, obj_in=tools_in, modified_by=modified_by)
    return tool_data

@router.post("/delete", status_code=201, response_model=Tools,
# dependencies=[
    # Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.EDIT.name))
# ]
)
def delete_tool(
    *, request:Request,tools_in: ToolsDelete, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Update a commodity in the database.
    provide fields which need to be updtaed and id is must needed
    """
    current_user: User = get_current_user(request)
    # modified_by = current_user.id 
    result = crud.tools.remove(db=db, id=tools_in.id)
    # tool_data = crud.tools.update(db=db, db_obj=result, obj_in=tools_in, modified_by=modified_by)
    return result






@router.get("/{tool_id}", status_code=200, response_model=Tools,
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.VIEW.name))
# ]
)
def fetch_tool_by_id(
    *,
    tool_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch a single tool by ID
    """
    result = crud.tools.get(db=db, id=tool_id)
    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        return {}
    return result

# @router.delete('/{tool_id}',
# # dependencies=[
# #     Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.DELETE.name))
# # ]
# )
# def delete_tool(
#     *,
#     tool_id: int,
#     db: Session = Depends(deps.get_db)
# ):
#     result = crud.tools.remove(db=db, id=tool_id)

#     if result is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail="Resource Not Found")
#     return result



