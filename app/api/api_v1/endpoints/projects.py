from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Any, List


from app import crud
from app.api import deps
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.schemas.designation_tools import DesignationTools
from app.schemas.designation_tools import DesignationToolsBase
from app.schemas.projects import ProjectDelete, ProjectTools, ProjectToolsAssignment, Projects, ProjectCreate, ProjectUpdate
from app.models.user import User
from app.schemas.tools import ToolsInDBBase
# from dateutil import parser
from app.util.user_util import get_current_user

router = APIRouter()

@router.post("/", status_code=201, response_model=Projects,dependencies=[
    # Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.ADD.name))
])
def create_projects(
    *, request: Request,projects_in: ProjectCreate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Create a new project in the database.
    """
    current_user: User = get_current_user(request)
    created_by = current_user.id 
    # user_in.expiry_date = parser.parse(user_in.expiry_date)
    prjs = crud.projects.create(db=db, obj_in=projects_in,created_by=created_by)
    return prjs

@router.get("/getall", status_code=200, response_model=List[Projects],dependencies=[
    # Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.VIEW.name))
])
def get_tools(
    *,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch a all projects
    """
    result = crud.projects.get_multi(db=db)
    if not result:
        return []
    return result


@router.post("/update", status_code=201, response_model=Projects,
# dependencies=[
    # Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.EDIT.name))
# ]
)
def update_project(
    *, request:Request,projects_in: ProjectUpdate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Update a commodity in the database.
    provide fields which need to be updtaed and id is must needed
    """
    current_user: User = get_current_user(request)
    modified_by = current_user.id 
    result = crud.projects.get(db=db, id=projects_in.id)
    project_data = crud.projects.update(db=db, db_obj=result, obj_in=projects_in, modified_by=modified_by)
    return project_data


@router.post("/delete", status_code=201, response_model=Projects,
# dependencies=[
    # Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.EDIT.name))
# ]
)
def delete_project(
    *, request:Request,projects_in: ProjectDelete, db: Session = Depends(deps.get_db)
) -> dict:
    """
    delete project in the database.
    provide fields which need to be updtaed and id is must needed
    """
    current_user: User = get_current_user(request)
    # modified_by = current_user.id 
    result = crud.projects.remove(db=db, id=projects_in.id)
    return result


@router.get("/{project_id}", status_code=200, response_model=Projects,
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.VIEW.name))
# ]
)
def fetch_project_by_id(
    *,
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch a single project by ID
    """
    result = crud.projects.get(db=db, id=project_id)
    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        return {}
    return result

@router.delete('/{project_id}',
# dependencies=[
#     Depends(PermissionChecker(module=ModulesEnum.PERMISSION.name,permission=PermissionsEnum.DELETE.name))
# ]
)
def delete_project(
    *,
    tool_id: int,
    db: Session = Depends(deps.get_db)
):
    result = crud.projects.remove(db=db, id=tool_id)

    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Resource Not Found")
    return result



# For project
@router.get("/{project_id}/tools", status_code=200, response_model=ProjectTools,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.VIEW.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.VIEW.name))
                # ]
                )
def fetch_assigned_tools(
    *,
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch assigned tools for project
    """
    result = crud.projects.get_assigned_tools(db=db, id=project_id)

    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        raise HTTPException(
            status_code=404, detail=f"User with ID {project_id} not found"
        )

    return result

@router.post("/{project_id}/tools", status_code=201, response_model=Projects,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.ADD.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.ADD.name))
                # ]
                )
def create_project_tools(
    *, project_id: int,project_in: ProjectToolsAssignment, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Assign tools to project
    """
    user = crud.projects.assign_tools(db=db, obj_in=project_in, project_id = project_id)

    return user

@router.post("/{project_id}/designations/tools", status_code=201, response_model=dict,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.ADD.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.ADD.name))
                # ]
                )
def create_designations_tools(
    *, project_id: int,desig_tools_in: List[DesignationTools], db: Session = Depends(deps.get_db)
) -> dict:
    """
    Assign tools to project
    """
    user = crud.projects.assign_desn_tools(db=db, obj_in=desig_tools_in, project_id = project_id)

    return {"success": True}

@router.get("/{project_id}/designations/tools", response_model=dict,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.ADD.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.ADD.name))
                # ]
                )
def get_designations_tools(
    *, project_id: int,designation_id: int, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Assign tools to project
    """
    desn_tools = crud.projects.get_desn_tools(db=db,project_id = project_id, designation_id=designation_id)

    return desn_tools

@router.get("/{project_id}/designations/all_tools", status_code=201, response_model=List[dict],
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.ADD.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.ADD.name))
                # ]
                )
def get_all_designations_tools(
    *, project_id: int, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Assign tools to project
    """
    desn_tools = crud.projects.get_all_desn_tools(db=db,project_id = project_id)

    return desn_tools



# @router.post("/{user_id}/project/delete", status_code=201, response_model=User,
#                 # dependencies=[
#                 #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.DELETE.name)),
#                 #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.DELETE.name))
#                 # ]
#                 )
# def delete_assigned_project(
#     *, user_id: int,project_in: UserProjectAssignment, db: Session = Depends(deps.get_db)
# ) -> dict:
#     """
#     Delete asiigned project for user.
#     """
#     user = crud.user.delete_assigned_project(db=db, obj_in=project_in, user_id = user_id)
    
#     return user

@router.get("/{project_id}/tools/notassociate", status_code=200, response_model=List[ToolsInDBBase],
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.VIEW.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.VIEW.name))
                # ]
                )
def fetch_not_associated_tools(
    *,
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch all roles which are not associated to this user
    """
    result = crud.projects.get_not_associated_tools(db=db, id=project_id)

    # if not result:
    #     # the exception is raised, not returned - you will get a validation
    #     # error otherwise.
    #     raise HTTPException(
    #         status_code=404, detail=f"User with ID {user_id} not found"
    #     )

    return result


