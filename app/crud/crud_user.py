from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.core.security import get_password_hash

from app.crud.base import CRUDBase
from app.models.permission import Permission
from app.models.roles import Roles
from app.models.projects import Projects
from app.models.user import User
from app.schemas.user import UserCreate, UserProjectAssignment, UserRoleAssignment, UserUpdate
from app.schemas.user import User as UserSchema


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get(self, db: Session, id: Any) -> Optional[User]:
        return db.query(User).filter(User.id == id).first()
    
    def get_by_emp_id(self, db: Session, emp_id: Any) -> Optional[User]:
        return db.query(User).filter(User.employee_id == emp_id).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_id(self, db: Session, *, id: int) -> Optional[User]:
        return db.query(User).filter(User.id == id).first()

    def create(self, db: Session, *, obj_in: UserCreate, created_by=None) -> User:
        obj_in.password = get_password_hash(obj_in.password)
        obj_in_data = jsonable_encoder(obj_in)
        obj_in_data["created_by"] = created_by
        db_obj = self.model(**obj_in_data)  # type: ignore
        # print(db_obj.last_login_date)

        # db_obj.last_login_date = datetime.strptime(
        #     db_obj.last_login_date, "%Y-%m-%dT%H:%M:%S.%f")
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[User, Dict[str, Any]], modified_by=None
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        return super().update(db, db_obj=db_obj, obj_in=update_data, modified_by=modified_by)

    def is_superuser(self, user: User) -> bool:
        return user.is_admin

    # def get_all_user_permissions(self, db: Session, user: User):
    #     return db.query(Permission.code).join(Roles, User.roles).join(Permission, Roles.permission).filter(User.id == user.id).all()

    def assign_role(self, db: Session, obj_in: UserRoleAssignment, user_id: int):
        role_obj = db.query(Roles).filter(Roles.id == obj_in.role_id).first()
        user_obj: UserSchema = db.query(User).filter(User.id == user_id).first()
        user_obj.roles.append(role_obj)
        db.add_all([user_obj])
        db.commit()
        db.refresh(user_obj)
        return user_obj

    def get_assigned_role(self, db: Session, id: int):
        user_obj: UserSchema = db.query(User).filter(User.id == id).first()
        return user_obj

    def delete_assigned_role(self, db: Session, obj_in: UserRoleAssignment, user_id: int):
        role_obj = db.query(Roles).filter(Roles.id == obj_in.role_id).first()
        user_obj: UserSchema = db.query(User).filter(User.id == user_id).first()
        user_obj.roles.remove(role_obj)
        db.add_all([user_obj])
        db.commit()
        db.refresh(user_obj)
        return user_obj

    def get_not_associated_roles(self, db: Session, id: int):
        users_obj = db.query(Roles).join(Roles, User.roles).filter(User.id == id).all()
        roles_obj_not_associated = db.query(Roles).all()
        for roles in users_obj:
            roles_obj_not_associated.remove(roles)
        return roles_obj_not_associated

    # def get_subscriber_data(self, db: Session, user_id: int):
    #     user_obj: UserSchema = db.query(User).filter(User.id == user_id).first()
    #     commodity_obj = db.query(Commodity).join(Subscriber.commodity).filter(Subscriber.id==user_obj.subscriber_id).all()
    #     lookahead_obj = db.query(Lookahead).join(Subscriber.lookahead).filter(Subscriber.id==user_obj.subscriber_id).all()
    #     commodity_list = [
    #         commodity.code for commodity in commodity_obj]
    #     lookahead_list = [
    #         lookahead.days for lookahead in lookahead_obj]
    #     # roles_obj_not_associated = db.query(Roles).all()
    #     # for roles in users_obj:
    #     #     roles_obj_not_associated.remove(roles)

    #     return UserSubscriptionData(commodity=commodity_list, lookahead_days=lookahead_list)

    def get_assigned_project(self, db: Session, id: int):
        user_obj: UserSchema = db.query(User).filter(User.id == id).first()
        return user_obj

    def assign_project(self, db: Session, obj_in: UserProjectAssignment, user_id: int):
        project_obj = db.query(Projects).filter(Projects.id == obj_in.project_id).first()
        user_obj: UserSchema = db.query(User).filter(User.id == user_id).first()
        user_obj.projects.append(project_obj)
        db.add_all([user_obj])
        db.commit()
        db.refresh(user_obj)
        return user_obj
    
    def delete_assigned_project(self, db: Session, obj_in: UserProjectAssignment, user_id: int):
        project_obj = db.query(Projects).filter(Projects.id == obj_in.project_id).first()
        user_obj: UserSchema = db.query(User).filter(User.id == user_id).first()
        user_obj.projects.remove(project_obj)
        db.add_all([user_obj])
        db.commit()
        db.refresh(user_obj)
        return user_obj


    def get_not_associated_projects(self, db: Session, id: int):
        users_obj = db.query(Projects).join(Projects, User.projects).filter(User.id == id).all()
        projects_obj_not_associated = db.query(Projects).all()
        for projects in users_obj:
            projects_obj_not_associated.remove(projects)
        return projects_obj_not_associated
        
    def get_configuration_user(self,db: Session, id):
        configuration_user_ids= db.execute("select ur.user_id from public.user_roles as ur JOIN public.roles as r on r.id=ur.role_id where r.name in ('COFIGURATION_MANAGER')").fetchall()
        ids = (",").join([str(data[0]) for data in configuration_user_ids]) 
        # tuple([data[0] for data in configuration_user_ids])
        configuration_users = db.execute(f"select u.id, u.first_name, u.last_name, u.employee_id, u.email, u.phone from public.user as u INNER JOIN public.user_projects as up On up.user_id=u.id where up.project_id={id} and u.id in ({ids});").mappings().all()
        return configuration_users

user = CRUDUser(User)
