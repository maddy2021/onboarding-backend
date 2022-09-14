# import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Any, List
from app import crud
from app.api import deps
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.schemas.projects import ProjectInDBBase
from app.schemas.roles import RoleInDBBase
from app.schemas.user import AccessRequest, ConfigUsers, UserBase, UserCreate, User, UserDelete, UserOnly, UserProject, UserProjectAssignment, UserRole, UserRoleAssignment, UserSearchResults, UserUpdate
from app.util.user_util import get_current_user
# logger = logging.getLogger(__name__)  # the __name__ resolve to "uicheckapp.services"
#                                       # This will load the uicheckapp logger


import win32com.client as win32
from datetime import datetime
import pythoncom
import os
from app.core.config import settings

router = APIRouter()

kt_data = settings.template_data

@router.post("/", status_code=201, response_model=UserOnly,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.ADD.name))
                # ]
                )
def create_user(
    *,request:Request, user_in: UserCreate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Create a new user in the database.
    """
    current_user: User = get_current_user(request)
    created_by = current_user.id 
    user = crud.user.create(db=db, obj_in=user_in, created_by=created_by)

    return user

@router.get("/getById/{user_id}", status_code=200, response_model=User,
            # dependencies=[
            #         Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.VIEW.name))
            #     ]
                )
def fetch_user_by_id(
    *,
    user_id: int,
    db: Session = Depends(deps.get_db),
    # permission: PermissionChecker = 
) -> Any:
    """
    Fetch a single user by ID
    """
    result = crud.user.get(db=db, id=user_id)
    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        return {}

    return result

@router.get("/getByEmpId/{employee_id}", status_code=200, response_model=User,
            # dependencies=[
            #         Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.VIEW.name))
            #     ]
                )
def fetch_employee_by_id(
    *,
    employee_id: int,
    db: Session = Depends(deps.get_db),
    # permission: PermissionChecker = 
) -> Any:
    """
    Fetch a single user by ID
    """
    result = crud.user.get_by_emp_id(db=db, employee_id=employee_id)
    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        raise HTTPException(
            status_code=404, detail=f"User with employee ID {employee_id} not found"
        )

    return result

@router.get("/getall", status_code=200, response_model=List[User],
                # UserOnly
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.VIEW.name))
                # ]
                )
# dependencies=[Depends(user_permissions.get_all_user_permission)]
def fetch_all_users(
    *,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch all users
    """
    # logger.info("getting all users")
    users = crud.user.get_multi(db=db)
    # s
    if not users:
        return []
    return users

@router.post("/update", status_code=201, response_model=UserOnly,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.EDIT.name))
                # ]
                )
def update_user(
    *,request:Request ,user_in: UserUpdate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Update a new user in the database.
    provide fields which need to be updtaed and id is must needed
    """
    current_user: User = get_current_user(request)
    modified_by = current_user.id
    result = crud.user.get(db=db, id=user_in.id)
    user = crud.user.update(db=db, db_obj=result, obj_in=user_in,modified_by=modified_by)

    return user

@router.post("/delete", status_code=201, response_model=UserOnly,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.EDIT.name))
                # ]
                )
def delete_user(
    *,request:Request ,user_in: UserDelete, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Update a new user in the database.
    provide fields which need to be updtaed and id is must needed
    """
    current_user: User = get_current_user(request)
    # modified_by = current_user.id
    # result = crud.user.get(db=db, id=user_in.id)
    user = crud.user.remove(db=db, id=user_in.id)

    return user


@router.get("/getpermission", status_code=200)
# dependencies=[Depends(user_permissions.get_all_user_permission)]
def fetch_all_users(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch all users
    """
    # logger.info("getting all users")
    current_user: User = get_current_user(request)
    user_data:User=crud.user.get(db=db,id=current_user.id)
    module_permission = {}
    for roles in user_data.roles:
        role_permissions = crud.role_permission.get_permissions_by_role(db=db,id=roles.id)
        for data in role_permissions:
            if data[1].lower() in module_permission.keys():
                module_permission[data[1].lower()].add(data[0].lower())
            else:
                module_permission[data[1].lower()] = {data[0].lower()}

    # if not users:
    #     raise HTTPException(
    #         status_code=404, detail=f"Users not found"
    #     )
    for key,values in module_permission.items():
        module_permission[key] = list(values)
    return module_permission


# @router.get("/search/", status_code=200, response_model=UserSearchResults)
# def search_users(
#     *,
#     email: Optional[str] = Query(None),
#     # max_results: Optional[int] = 10,
#     db: Session = Depends(deps.get_db),
# ) -> dict:
#     """
#     Search for users based on label keyword
#     """
#     users = crud.user.get_multi(db=db)
#     if not email:
#         return {"results": users}

#     results = filter(lambda user: email.lower() in user.email.lower(), users)
#     return {"results": list(results)}


# @router.post("/", status_code=201, response_model=UserOnly,
#                 # dependencies=[
#                 #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.ADD.name))
#                 # ]
#                 )
# def create_user(
#     *,request:Request, user_in: UserCreate, db: Session = Depends(deps.get_db)
# ) -> dict:
#     """
#     Create a new user in the database.
#     """
#     current_user: User = get_current_user(request)
#     created_by = current_user.id 
#     user = crud.user.create(db=db, obj_in=user_in, created_by=created_by)

#     return user

@router.get("/{user_id}/role", status_code=200, response_model=UserRole,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.VIEW.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.VIEW.name))
                # ]
                )
def fetch_assigned_role(
    *,
    user_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch assigned role for user
    """
    result = crud.user.get_assigned_role(db=db, id=user_id)

    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        raise HTTPException(
            status_code=404, detail=f"User with ID {user_id} not found"
        )

    return result

@router.post("/{user_id}/role", status_code=201, response_model=User,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.ADD.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.ADD.name))
                # ]
                )
def create_subscriber(
    *, user_id: int,role_in: UserRoleAssignment, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Assign role to user
    """
    user = crud.user.assign_role(db=db, obj_in=role_in, user_id = user_id)

    return user

@router.post("/{user_id}/role/delete", status_code=201, response_model=User,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.DELETE.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.DELETE.name))
                # ]
                )
def delete_assigned_role(
    *, user_id: int,role_in: UserRoleAssignment, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Delete asiigned role for user.
    """
    user = crud.user.delete_assigned_role(db=db, obj_in=role_in, user_id = user_id)
    
    return user

@router.get("/{user_id}/role/notassociate", status_code=200, response_model=List[RoleInDBBase],
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.VIEW.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.VIEW.name))
                # ]
                )
def fetch_not_associated_roles(
    *,
    user_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch all roles which are not associated to this user
    """
    result = crud.user.get_not_associated_roles(db=db, id=user_id)

    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        raise HTTPException(
            status_code=404, detail=f"User with ID {user_id} not found"
        )

    return result

# For project
@router.get("/{user_id}/project", status_code=200, response_model=UserProject,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.VIEW.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.VIEW.name))
                # ]
                )
def fetch_assigned_project(
    *,
    user_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch assigned role for user
    """
    result = crud.user.get_assigned_project(db=db, id=user_id)

    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        raise HTTPException(
            status_code=404, detail=f"User with ID {user_id} not found"
        )

    return result

@router.post("/{user_id}/project", status_code=201, response_model=User,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.ADD.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.ADD.name))
                # ]
                )
def create_user_project(
    *, user_id: int,project_in: UserProjectAssignment, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Assign role to user
    """
    user = crud.user.assign_project(db=db, obj_in=project_in, user_id = user_id)

    return user

@router.post("/{user_id}/project/delete", status_code=201, response_model=User,
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.DELETE.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.DELETE.name))
                # ]
                )
def delete_assigned_project(
    *, user_id: int,project_in: UserProjectAssignment, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Delete asiigned project for user.
    """
    user = crud.user.delete_assigned_project(db=db, obj_in=project_in, user_id = user_id)
    
    return user

@router.get("/{user_id}/project/notassociate", status_code=200, response_model=List[ProjectInDBBase],
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.VIEW.name)),
                #     Depends(PermissionChecker(module=ModulesEnum.ROLE.name,permission=PermissionsEnum.VIEW.name))
                # ]
                )
def fetch_not_associated_projects(
    *,
    user_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch all roles which are not associated to this user
    """
    result = crud.user.get_not_associated_projects(db=db, id=user_id)

    # if not result:
    #     # the exception is raised, not returned - you will get a validation
    #     # error otherwise.
    #     raise HTTPException(
    #         status_code=404, detail=f"User with ID {user_id} not found"
    #     )

    return result

@router.get("/get_config_user/{project_id}", status_code=200, response_model=List[ConfigUsers],
            # dependencies=[
            #         Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.VIEW.name))
            #     ]
                )
def fetch_config_managers(
    *,
    project_id: int,
    db: Session = Depends(deps.get_db),
    # permission: PermissionChecker = 
) -> Any:
    """
    Fetch a single user by ID
    """
    result = crud.user.get_configuration_user(db=db,id=project_id)
    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        raise HTTPException(
            status_code=404, detail=f"Config user for project ID {project_id} not found"
        )

    return result



@router.post("/provide_access", status_code=201, response_model={},
                # dependencies=[
                #     Depends(PermissionChecker(module=ModulesEnum.USER.name,permission=PermissionsEnum.ADD.name))
                # ]
                )
def create_user(
    *,request:Request, req_in: AccessRequest, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Create a new user in the database.
    """
    current_user: User = get_current_user(request)
    # created_by = current_user.id 
    # user = crud.user.create(db=db, obj_in=user_in, created_by=created_by)
    print(req_in)
    kt_msg = "<ul>"
    for prj in req_in.projects:
        kt_obj = kt_data[prj]["kt_data"]
        for kt_dict in kt_obj:
            kt_msg = kt_msg + f"<li><a href={kt_dict['url']}>{kt_dict['name']}</a></li><br>"
        kt_msg=kt_msg+"</ul>"
    outlook = win32.Dispatch('outlook.application',pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)
    mail.Subject = 'Onboarding POC Test Mail - Approval Request For Project Tools'
    mail.To =  (';').join(req_in.configuration_user)+';'+req_in.email + ';' + current_user.email
    # mail.CC = current_user.email
    mail.HTMLBody = f" \
    Hello,<br><br> \
    This is onboarding poc test mail. <br>\
    Employee_id: {req_in.employee_id} <br> \
    {req_in.first_name} {req_in.last_name} need access for the {(', ').join(req_in.projects)} Project tools. Please provide access for below.<br><br> \
    {('<br/>').join(req_in.project_tools)} \
    <br><br> \
    Regards,<br> \
    {current_user.first_name} {current_user.last_name} \
    "
    mail.Send()
    # For KT links
    mail = outlook.CreateItem(0)
    mail.Subject = 'Onboarding POC Test Mail - Approval Request For Project Tools'
    mail.To =  (';').join(req_in.configuration_user)+';'+req_in.email + ';' + current_user.email
    # mail.CC = current_user.email
    mail.HTMLBody = f" \
    Hello,<br><br> \
    This is onboarding poc test mail. <br>\
    Employee_id: {req_in.employee_id} <br> \
    {req_in.first_name} {req_in.last_name} Please find the KT links: \
    {kt_msg}\
    <br><br> \
    Regards,<br> \
    {current_user.first_name} {current_user.last_name} \
    "
    mail.Send()
    return {}