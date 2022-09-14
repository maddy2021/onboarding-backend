from ast import List
from app.crud.base import CRUDBase
from sqlalchemy.orm import Session
from app.models.permission import Permission
from app.models.roles import Roles
from app.models.role_permission import RolePermission
from app.models.user import User
from app.schemas.role_permission import RolePermissionBase, RolePermissionIn
# from app.schemas.roles import AssignPermission, PermissionData, RoleCreate, RoleUpdate
from app.schemas.roles import RoleCreate, RoleUpdate
from app.schemas.roles import Role as RoleSchema


class CRUDRoles(CRUDBase[Roles, RoleCreate, RoleUpdate]):
    ...


roles = CRUDRoles(Roles)
