from ast import List
from app.crud.base import CRUDBase
from app.models.request_status import RequestStatus

# from app.schemas.roles import AssignPermission, PermissionData, RoleCreate, RoleUpdate
from app.schemas.request_status import RequestStatusCreate, RequestStatusUpdate
from sqlalchemy.orm import Session


class CRUDReqStatus(CRUDBase[RequestStatus, RequestStatusCreate, RequestStatusUpdate]):
    def get_configuration_user(self,db: Session, id):
        configuration_user_ids= db.execute("select ur.user_id from public.user_roles as ur JOIN public.roles as r on r.id=ur.role_id where r.name in ('COFIGURATION_MANAGER')").fetchall()
        ids = (",").join([str(data[0]) for data in configuration_user_ids]) 
        # tuple([data[0] for data in configuration_user_ids])
        configuration_users = db.execute(f"select u.id, u.first_name, u.last_name, u.employee_id, u.email, u.phone from public.user as u INNER JOIN public.user_projects as up On up.user_id=u.id where up.project_id={id} and u.id in ({ids});").mappings().all()
        return configuration_users


req_status = CRUDReqStatus(RequestStatus)
