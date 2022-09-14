
from enum import Enum
from typing import List
from fastapi import Depends, Request
from sqlalchemy import false
from app.api import deps
from app import crud
from app.schemas.user import User
from app.util.json_encode_util import authorization_fail
from app.util.user_util import get_current_user, get_current_user_permission
from sqlalchemy.orm import Session


class ModulesEnum(Enum):
    ADMIN = 1
    USER = 2
    SUBSCRIBER = 3
    COMMODITY = 4
    ROLE = 5
    ACTIVE_COMMODITY = 6
    LOOKAHEAD = 7
    PERMISSION = 8
    PDESK = 9
    BACKTEST = 10
    COMPLETE_HISTORY_BACKTEST_METRIC = 11,
    FEATURE_IMPORTANCE = 12,
    DAILY_PREDICTION = 13,
    HISTORICAL_VOLATILITY = 14,
    BASIS_RISK = 15,
    FEATURE_FOR_INSTRUMENTS = 16,
    PUBLIC_POSTING_MONTH_IN = 17,
    PUBLIC_POSTING_MONTH_FOR = 18,
    WHAT_IF = 19
    Spread = 20

class PermissionsEnum(Enum):
    VIEW = 1
    ADD = 2
    EDIT = 3
    DELETE = 4
    EXPORT = 5


class PermissionChecker:
    def __init__(self, permission: str, module: str):
        self.permission = permission.lower()
        self.module = module.lower()

    def __call__(self, request: Request, db: Session = Depends(deps.get_db)):
        print("Has Permission Dependencies")
        current_user: User = get_current_user(request)
        if current_user.is_super_admin:
            return
        user_data:User=crud.user.get(db=db,id=current_user.id)
        module_permission = {}
        for roles in user_data.roles:
            role_permissions = crud.role_permission.get_permissions_by_role(db=db,id=roles.id)
            for data in role_permissions:
                if data[1].lower() in module_permission.keys():
                    module_permission[data[1].lower()].add(data[0].lower())
                else:
                    module_permission[data[1].lower()] = {data[0].lower()}
        
        has_permission = False
        if(self.module in module_permission.keys()):
            has_permission = self.permission in module_permission[self.module]

        if not has_permission:
            raise authorization_fail("Does not have privileges")
