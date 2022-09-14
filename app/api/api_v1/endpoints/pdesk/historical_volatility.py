from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Any, List
from app.CustomErrors.HTTPErrors.http_base_error import CustomError, InternalServerError, PermissionDeniedError
from app.api import deps
from app.core.cache import get_cache, set_cache
from app.core.config import settings
from app.core.helper import filter_subscribed_commodities
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.helpers.pdesk.backtest.historical_volatility_helper import create_graph_data
from app.schemas.charts import DropDownModel

from app.schemas.pdesk import FinalChartData
from app.util.query import get_data_single_filter
from app.util import common

router = APIRouter()

inference_features = settings.template_data["pdesk"]["historical_volatility"]
y_variable = inference_features["y_variable"]
operations = inference_features["operations"]
model_type = inference_features["model_type"]
pdesk_hist_vol_redis_prefix = "pdesk_his_vol"

def fetch_last_updated(db: Session) -> Any:
    """
    Get last updated date
    """
    try:
        result = get_data_single_filter("last_updated_date","pdesk_basisrisk")
        updated_date = str(result[0][0])
        return updated_date
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error while getting updated date")  

@router.get("/y-variables", status_code=200, response_model=List[DropDownModel])
def fetch_y_variable(*, request: Request, db: Session = Depends(deps.get_db)) -> Any:
    """
    Dropdown Values for Y-variable(commodity)
    """
    dropDownList: List[DropDownModel] = filter_subscribed_commodities(
        request=request, y_variable=y_variable, db=db)
    return dropDownList


@router.get("/operations", status_code=200)
def fetch_operations() -> Any:
    """
    Dropdown Values for operations
    """
    dropDownList = common.dropDownFormatter(input_list=operations)
    return dropDownList

# In future take edibleoil as path or query parameter 
@router.get("/edibleoil-volatility/chart", status_code=200, response_model=FinalChartData, response_model_exclude_unset=True,dependencies=[Depends(PermissionChecker(module=ModulesEnum.HISTORICAL_VOLATILITY.name,permission=PermissionsEnum.VIEW.name))])
def fetch_graph(*,db: Session = Depends(deps.get_db_1),
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    operation:str = Query("MEAN"),
    request: Request, admin_db: Session = Depends(deps.get_db)) -> Any:  
    """
    Fetch historical volatility graph
    """
    date_key = common.today_date_key()
    error_list = []
    if(operation not in operations):
        error_list.append(CustomError(["query_param","operation"], ValueError("invalid entry for operation")))
    if(label not in [y["value"] for y in  filter_subscribed_commodities(request=request, y_variable=y_variable, db=admin_db)]):
        error_list.append(CustomError(["query_param","label"], ValueError("invalid entry for commodity"))) 
    if(error_list):
        raise PermissionDeniedError(error_list)       
    try:
        label_value = label
        label_name = ""
        for data in y_variable:
            if(data["value"]==label_value):
                label_name = data["label"].replace("-"," ")
                break
        redis_key = f"{pdesk_hist_vol_redis_prefix}_edibl_vol_chart_{date_key}_{label_value}_{operation}"
        graph_data = get_cache(redis_key)
        if(not graph_data):
            updated_date = fetch_last_updated(db=db)
            graph_data = create_graph_data(label_value,label_name,operation,updated_date)
            set_cache(redis_key,graph_data,expiry_time=settings.time_to_expire)
        return graph_data
    except Exception as e:
        print(e)
        error_list.append(CustomError(error_loc=["internal_server"],error_object=Exception("Not able to generate chart for edibleoil-volatility")))
        raise InternalServerError(error_list)  
