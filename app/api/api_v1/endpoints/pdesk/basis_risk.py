from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Any, List
from app.CustomErrors.HTTPErrors.http_base_error import CustomError, InternalServerError, PermissionDeniedError
from app.api import deps
from app.core.cache import get_cache, set_cache
from app.core.config import settings
from app.core.helper import filter_subscribed_commodities
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.helpers.pdesk.backtest.basis_risk_helper import create_graph_data
from app.schemas.charts import DropDownModel

from app.schemas.pdesk import FinalChartData
from app.util.common import today_date_key
from app.util.query import get_data_single_filter

router = APIRouter()

inference_features = settings.template_data["pdesk"]["basis_risk"]
y_variable = inference_features["y_variable"]
model_type = inference_features["model_type"]
pdesk_basis_risk_redis_prefix = "pdesk_bs" 


def fetch_last_updated( db: Session) -> Any:
    """
    Get last updated date
    """
    result = get_data_single_filter("last_updated_date","pdesk_basisrisk")
    updated_date = str(result[0][0])
    return updated_date


@router.get("/y-variables", status_code=200,response_model=List[DropDownModel])
def fetch_y_variable(*, request: Request, db: Session = Depends(deps.get_db)) -> Any:
    """
    Dropdown Values for Y-variable(commodity)
    """
    dropDownList: List[DropDownModel] = filter_subscribed_commodities(
        request=request, y_variable=y_variable, db=db)
    return dropDownList

# Todo take india as path or query parameter in future
@router.get("/india/chart", status_code=200, response_model=FinalChartData, response_model_exclude_unset=True, dependencies=[Depends(PermissionChecker(module=ModulesEnum.BASIS_RISK.name,permission=PermissionsEnum.VIEW.name))])
def fetch_graph(*, request: Request ,db: Session = Depends(deps.get_db_1),admin_db: Session = Depends(deps.get_db),
    label: str = Query("Correlation between 3-CPO(BMD) and Spot-CPO(BMD)"),) -> Any:  
    """
    Fetch historical volatility graph
    """
    date_key = today_date_key()
    
    # Need to do work here
    if(label not in [y["value"] for y in filter_subscribed_commodities(
        request=request, y_variable=y_variable, db=admin_db)]):
        raise PermissionDeniedError([CustomError(error_loc=["query_param","label"],error_object=ValueError("Invalid entry for commodity"))])
    try:
        label_value = label
        redis_key = f"{pdesk_basis_risk_redis_prefix}_india_chart_{date_key}_{label_value}"
        graph_data = get_cache(redis_key)
        updated_date = fetch_last_updated(db=db)
        if(not graph_data):
            graph_data = create_graph_data(label_value, updated_date)
            set_cache(redis_key, graph_data, expiry_time=settings.time_to_expire)
        return graph_data
    except Exception as e:
        print(e)
        raise InternalServerError([CustomError(error_loc=["internal_server"],error_object=Exception("Error while generating basis risk india chart"))])
