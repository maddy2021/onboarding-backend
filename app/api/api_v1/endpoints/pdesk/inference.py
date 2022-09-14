from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Any, List
from app.CustomErrors.HTTPErrors.http_base_error import CustomError, InternalServerError, PermissionDeniedError
from app.api import deps
from app.core.cache import get_cache, set_cache
from app.core.config import settings
from app.core.helper import filter_subscribed_commodities
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.helpers.pdesk.backtest.inference_helper import create_graph_data, create_table_data, get_date_range
from app.schemas.charts import DropDownModel
from app.schemas.pdesk import FinalChartData,TableData
from app.util.query import get_data_single_filter, getactivecontractsoyoil
from app.util import common


router = APIRouter()

inference_features = settings.template_data["pdesk"]["inference"]
y_variable = inference_features["y_variable"]
currency_list = inference_features["currency"]
model_type = inference_features["model_type"]
pdesk_infer_redis_prefix = "pdesk_infer"

def fetch_last_updated(  db: Session) -> Any:
    """
    Fetch a variable list
    """
    try:
        result = get_data_single_filter("last_updated_date","Pdesk_daily_prediction")
        updated_date = str(result[0][0])
        return updated_date
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error while getting updated date")  

@router.get("/y-variables", status_code=200, response_model=List[DropDownModel])
def fetch_y_variable( * ,db: Session = Depends(deps.get_db_1), request: Request, admin_db: Session = Depends(deps.get_db)) -> Any:
    """
    Dropdown Values for Y-variable(commodity)
    """
    commodities = filter_subscribed_commodities(request=request, y_variable=y_variable, db=admin_db)
    is_3_month_active = getactivecontractsoyoil('pdesk_edibleoil_daily_features')

    if is_3_month_active:
        y_var: List[DropDownModel] = [item for item in commodities if (item['label']!='2-Soyoil(CBOT)' and item['label']!='Basis-Argentina_Soyoil-2Soyoil(CBOT)')]
    else:
        y_var: List[DropDownModel] = [item for item in commodities if (item['label']!='3 Soyoil(CBOT)' and item['label']!='Basis-Argentina_Soyoil-3Soyoil(CBOT)')]
    return y_var


@router.get("/dates", status_code=200, response_model=List[DropDownModel])
def fetch_dates() -> Any:
    """
    Dropdown for date_range
    """
    today_date = datetime.today()

    date_list = get_date_range(today_date, 30, is_reverse=True, exclude_weekdays=[6,0])

    str_date_list = []

    for i_date in date_list:
        label = i_date.strftime("%d-%m-%Y")
        value = i_date.strftime("%d_%m_%Y")
        str_date_list.append({"label": label, "value": value})
    return str_date_list

@router.get("/currencies", status_code=200,response_model=List[DropDownModel])
def fetch_currency() -> Any:
    """
    Dropdown Values for Currency
    """
    dropDownList = common.dropDownFormatter(input_list=currency_list)
    return dropDownList

@router.get("/daily-prediction/chart", status_code=200, response_model=FinalChartData, response_model_exclude_unset=True, dependencies=[Depends(PermissionChecker(module=ModulesEnum.DAILY_PREDICTION.name,permission=PermissionsEnum.VIEW.name))])
def fetch_graph(*,
    db: Session = Depends(deps.get_db_1),
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    date_value: str,
    currency:str = Query("$/MT"),
    request: Request, admin_db: Session = Depends(deps.get_db)) -> Any:  
    """
    get daily prediction chart
    """
    date_key = common.today_date_key()
   
    error_list = []
    if(currency not in currency_list):
        error_list.append(CustomError(["query_param","currency"], ValueError("invalid entry for currency")))
    if(label not in [y["value"] for y in filter_subscribed_commodities(request=request, y_variable=y_variable, db=admin_db)]):
        error_list.append(CustomError(["query_param","label"], ValueError("invalid entry for commodity")))
    if(error_list):
        raise PermissionDeniedError(error_list)      
    try:
        label_value = label
        redis_key = f"{pdesk_infer_redis_prefix}_daily_pred_chart_{date_key}_{label_value}_{date_value}_{currency}"
        graph_data = get_cache(redis_key)
        if(not graph_data):
            last_updated_date = fetch_last_updated(db=db)
            graph_data = create_graph_data(label_value,date_value,currency,last_updated_date)
            set_cache(redis_key,graph_data,expiry_time=settings.time_to_expire)
        return graph_data
    except Exception as e:
        print(e)
        error_list.append(CustomError(error_loc=["internal_server"],error_object=Exception("Not able to generate chart for daily-prediction")))
        raise InternalServerError(error_list)


@router.get("/daily-prediction", status_code=200, response_model=TableData, dependencies=[Depends(PermissionChecker(module=ModulesEnum.DAILY_PREDICTION.name,permission=PermissionsEnum.VIEW.name))])
def fetch_table(  *,
db: Session = Depends(deps.get_db_1),
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    date_value: str,
    currency:str = Query("$/MT"),
    request: Request, admin_db: Session = Depends(deps.get_db)) -> Any:
    """
    get daily prediction table data 
    """
    date_key = common.today_date_key()
    error_list = []
    last_updated_date = fetch_last_updated(db=db)
    if(currency not in currency_list):
        error_list.append(CustomError(["query_param","currency"], ValueError("invalid entry for currency")))
    if(label not in [y["value"] for y in filter_subscribed_commodities(request=request, y_variable=y_variable, db=admin_db)]):
        error_list.append(CustomError(["query_param","label"], ValueError("invalid entry for commodity")))
    if(error_list):
        raise PermissionDeniedError(error_list)  
    try:
        label_value = label
        redis_key = f"{pdesk_infer_redis_prefix}_daily_pred_table_{date_key}_{label_value}_{date_value}_{currency}"
        table_data = get_cache(redis_key)
        if(not table_data):
            table_data = create_table_data(label_value,date_value,currency,last_updated_date)
            set_cache(redis_key,table_data,expiry_time=settings.time_to_expire)
        return table_data
    except Exception as e:
        print(e)
        error_list.append(CustomError(error_loc=["internal_server"],error_object=Exception("Not able to generate table for daily-prediction")))
        raise InternalServerError(error_list)

