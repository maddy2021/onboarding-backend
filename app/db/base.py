# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.db.base_class import BaseDefault  # noqa
from app.models.user import User  # noqa
from app.models.roles import Roles
from app.models.permission import Permission
from app.models.projects import Projects
from app.models.tools import Tools
# from app.models.active_commodity import ActiveCommodity
from app.models.module import Module
from app.models.role_permission import RolePermission
from app.models.kt_links import KtLinks
from app.models.designations import Designations
from app.models.designation_tools import DesignationTools
from app.models.request_status import RequestStatus
