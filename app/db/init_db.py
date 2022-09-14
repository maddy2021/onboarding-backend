from copy import copy
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app import crud, schemas
# from app.db import base  # noqa: F401
from app.core.config import settings
# from app.schemas import roles
# from app.schemas.commodity import Commodity, CommodityCreate
# from app.schemas.module import ModuleCreate
# from app.schemas.permission import PermissionCreate


logger = logging.getLogger(__name__)

commodity_list = ['CPO-Malaysia-Spot', '2-Soyoil-CBOT', 'MCX-Spot', 'Basis-CPO-India-Spot-3-CPO-BMD', 
                '2-Soybean-NCDEX', '2-Soybean-NCDEX-Soybean-NCDEX-Spot', 'Basis-Soyoil-Argentina-2-Soyoil-CBOT', 
                'Basis-Soyoil-Argentina-3-Soyoil-CBOT', '3-Soyoil-CBOT', 'BMD-Spot', '3-Soyoil-CBOT-Soyoil-NCDEX-Spot', 
                'RMSeed-Spot','1-Soybean-NCDEX', 'Soybean-NCDEX-Spot', '2/3-Soyoil-CBOT', '1-RMSeed-NCDEX', 
                '3-CPO-BMD-CPO-MCX-Spot', '3-Soybean-CBOT-Soybean-NCDEX-Spot', '3-CPO-BMD-CPO-BMD-Spot', 
                '2-CPO-MCX', 'Basis-CPO-Malaysia-Spot-3-CPO-BMD', '2-CPO-MCX-CPO-MCX-Spot', '3-CPO-BMD', 
                '2-Soyoil-NCDEX-Soyoil-NCDEX-Spot', 'Soyoil-NCDEX-Spot', '2-Soyoil-NCDEX']

# make sure all SQL Alchemy models are imported (app.db.base) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28
def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)
    if settings.FIRST_SUPERUSER:
        user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)
        if not user:
            user_in = schemas.UserCreate(
                first_name="root_admin",
                employee_id = 223456,
                email=settings.FIRST_SUPERUSER,
                email_confirmed=False,
                password="password",
                phone="9898123456",
                phone_confirmed=False,
                lockout_end=None,
                is_super_admin=True,
                last_login_date=datetime.now(),
            )
            user = crud.user.create(db, obj_in=user_in)  # noqa: F841
            user_data = copy(user)
            user_data.modified_by = user.id
            user_data.created_by = user.id
            user = crud.user.update(
                db, db_obj=user, obj_in=user_data.__dict__, modified_by=user.id)

            # # Script to add permissions
            # crud.permission.create(db, obj_in= PermissionCreate(
            #     code="VIEW", display_name="view"), created_by= user.id)
            # crud.permission.create(db, obj_in= PermissionCreate(
            #     code="ADD", display_name="add"), created_by= user.id)
            # crud.permission.create(db, obj_in= PermissionCreate(
            #     code="EDIT", display_name="edit"), created_by= user.id)
            # crud.permission.create(db, obj_in= PermissionCreate(
            #     code="DELETE", display_name="delete"), created_by= user.id)
            # crud.permission.create(db, obj_in= PermissionCreate(
            #     code="EXPORT", display_name="export"),created_by= user.id)

            # # Script to add modules
            # admin_parent_module: Commodity = crud.module.create(db, obj_in=ModuleCreate(
            #     code="ADMIN", display_name="admin", parent_id=None, sequence=1, is_header=True), created_by=user.id)

            # crud.module.create(db, obj_in=ModuleCreate(code="USER", display_name="user",
            #                    parent_id=admin_parent_module.id, sequence=1.1, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="SUBSCRIBER", display_name="subscriber",
            #                    parent_id=admin_parent_module.id, sequence=1.2, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="COMMODITY", display_name="commodity",
            #                    parent_id=admin_parent_module.id, sequence=1.3, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="ROLE", display_name="role",
            #                    parent_id=admin_parent_module.id, sequence=1.4, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="LOOKAHEAD", display_name="lookahead",
            #                    parent_id=admin_parent_module.id, sequence=1.5, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="PERMISSION", display_name="permission",
            #                    parent_id=admin_parent_module.id, sequence=1.6, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="ACTIVE_COMMODITY", display_name="active_commodity",
            #                    parent_id=admin_parent_module.id, sequence=1.7, is_header=False), created_by=user.id)

            # pdesk_parent_module: Commodity = crud.module.create(db, obj_in=ModuleCreate(
            #     code="PDESK", display_name="pdesk", parent_id=None, sequence=2, is_header=True), created_by=user.id)

            # crud.module.create(db, obj_in=ModuleCreate(code="BACKTEST", display_name="backtest",
            #                    parent_id=pdesk_parent_module.id, sequence=2.1, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="COMPLETE_HISTORY_BACKTEST_METRIC", display_name="complete_history_backtest_metric",
            #                    parent_id=pdesk_parent_module.id, sequence=2.2, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="FEATURE_IMPORTANCE", display_name="feature_importance",
            #                    parent_id=pdesk_parent_module.id, sequence=2.3, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="DAILY_PREDICTION", display_name="daily_prediction",
            #                    parent_id=pdesk_parent_module.id, sequence=2.4, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="HISTORICAL_VOLATILITY", display_name="historical_volatility",
            #                    parent_id=pdesk_parent_module.id, sequence=2.5, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="BASIS_RISK", display_name="basis_risk",
            #                    parent_id=pdesk_parent_module.id, sequence=2.6, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="FEATURE_FOR_INSTRUMENTS", display_name="feature_for_instruments",
            #                    parent_id=pdesk_parent_module.id, sequence=2.7, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="PUBLIC_POSTING_MONTH_IN", display_name="public_posting_month_in",
            #                    parent_id=pdesk_parent_module.id, sequence=2.8, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="PUBLIC_POSTING_MONTH_FOR", display_name="public_posting_month_for",
            #                    parent_id=pdesk_parent_module.id, sequence=2.9, is_header=False), created_by=user.id)
            # crud.module.create(db, obj_in=ModuleCreate(code="WHAT_IF", display_name="what_if",
            #                    parent_id=pdesk_parent_module.id, sequence=2.10, is_header=False), created_by=user.id)

            # # Script to add commodity from list
            # for com_name in commodity_list:
            #     crud.commodity.create(db,obj_in =CommodityCreate(code=com_name,display_name=com_name),created_by=user.id)

        elif user:
            user_data = copy(user)
            print(user.id)
            user_data.created_by = user.id
            print(user_data.__dict__)
            user = crud.user.update(
                db, db_obj=user, obj_in=user_data.__dict__, modified_by=user.id)
        else:
            logger.warning(
                "Skipping creating superuser. User with email "
                f"{settings.FIRST_SUPERUSER} already exists. "
            )
    else:
        logger.warning(
            "Skipping creating superuser.  FIRST_SUPERUSER needs to be "
            "provided as an env variable. "
            "e.g.  FIRST_SUPERUSER=admin@api.coursemaker.io"
        )

# future task
# def add_commodity():
# def add_roles():
# def add_permissions():
