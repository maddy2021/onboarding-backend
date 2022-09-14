from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Any, List
from app.CustomErrors.HTTPErrors.http_base_error import CustomError, InternalServerError, PermissionDeniedError
from app.api import deps
from app.core.cache import get_cache, set_cache
from app.core.config import settings
from app.core.helper import filter_subscribed_commodities, filter_subscribed_lookahead_Days
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.helpers.pdesk.backtest.feature_list_helper import get_feature_importance, get_features
from app.schemas.charts import DropDownModel
from app.util import common
from app.helpers.pdesk.backtest.feature_explainability_helper import get_explainable_graph_data
from app.schemas.pdesk import FinalChartData, TableData
from app.util import common
from sqlalchemy.orm import Session



router = APIRouter()

instrument_features = settings.template_data["pdesk"]["instrument_features"]
feature_list_y_variable: List[DropDownModel] = instrument_features["feature_list"]["y_variable"]
soyoil_active_month = instrument_features["feature_list"]["soyoil_active_month"]
feature_importance_y_variable: List[DropDownModel] = instrument_features["feature_importance"]["y_variable"]
lookahead_days_list = instrument_features["feature_importance"]["lookahead"]

explainable_features = settings.template_data["pdesk"]["explainability"]
y_variable = explainable_features["y_variable"]
explainability_lookahead_days_list = explainable_features["lookahead"]

model_type = explainable_features["model_type"]
pdesk_feature_list_redis_prefix = "pdesk_fl" 


@router.get("/y-variables", status_code=200)
def fetch_y_variable(*, request: Request, db: Session = Depends(deps.get_db)) -> Any:
    """
    Dropdown Values of features for Y-variable(commodity)
    """
    y_variable= {
        "feature_list":  filter_subscribed_commodities(request=request, y_variable=feature_list_y_variable, db=db) ,
        "feature_importance": filter_subscribed_commodities(request=request, y_variable=feature_importance_y_variable, db=db)  
    }
    return y_variable


@router.get("/lookahead-days", status_code=200, response_model=List[DropDownModel])
def fetch_lookahead(*, request: Request, db: Session = Depends(deps.get_db)) -> Any:
    """
    Dropdown Values for lookahead days
    """
    lookahead_days = filter_subscribed_lookahead_Days(
        request=request, lookahead_days=lookahead_days_list, db=db)
    dropDownList = common.dropDownFormatter(input_list=lookahead_days)
    return dropDownList

@router.get("/active-months", status_code=200, response_model=List[DropDownModel])
def fetch_active_months() -> Any:
    """
    Dropdown Values for soyoil_active_month
    """
    dropDownList = common.dropDownFormatter(input_list=soyoil_active_month)
    return dropDownList

@router.get("/instruments", status_code=200, response_model=TableData,dependencies=[Depends(PermissionChecker(module=ModulesEnum.FEATURE_FOR_INSTRUMENTS.name,permission=PermissionsEnum.VIEW.name))])
def fetch_feature_table(*,
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    active_month: int = Query(2),
    request: Request, db: Session = Depends(deps.get_db)) -> Any:  
    """
    Get Table for features
    """
    date_key = common.today_date_key()
    
    error_list = []
    if(active_month not in soyoil_active_month):
        error_list.append(CustomError(error_loc=["query_param","active_month"],error_object=ValueError("Invalid entry for active month")))
    if(label not in [y["value"] for y in filter_subscribed_commodities(request=request, y_variable=feature_list_y_variable, db=db)]):
        error_list.append(CustomError(error_loc=["query_param","label"],error_object=ValueError("Invalid entry for commodity")))
    if error_list:
        raise PermissionDeniedError(error_list)   
    try:
        label_value = label
        redis_key = f"{pdesk_feature_list_redis_prefix}_instru_table_{date_key}_{label_value}_{active_month}"
        feature_importance = get_cache(redis_key)
        if(not feature_importance):
            feature_importance = get_features(label_value,active_month)
            set_cache(redis_key,feature_importance,expiry_time=settings.time_to_expire)
        return feature_importance
    except Exception as e:
        print(e)
        error_list.append(CustomError(error_loc=["internal_server"],error_object=Exception("Not able to generate table for instruments")))
        raise InternalServerError(error_list)   

@router.get("/importance", status_code=200, response_model=TableData, dependencies=[Depends(PermissionChecker(module=ModulesEnum.FEATURE_FOR_INSTRUMENTS.name,permission=PermissionsEnum.VIEW.name))])
def fetch_feature_importance(  *,
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    lookahead: int = Query(15),
    request: Request, db: Session = Depends(deps.get_db)) -> Any:
    """
    Get Table for feature importance
    """
    date_key = common.today_date_key()
    
    error_list = []
    if(lookahead not in filter_subscribed_lookahead_Days(request=request, lookahead_days=lookahead_days_list, db=db)):
        error_list.append(CustomError(["query_param","lookahead"],ValueError("invalid entry for lookahead days"))) 
    if(label not in [y["value"] for y in filter_subscribed_commodities(request=request, y_variable=feature_importance_y_variable, db=db)]):
        error_list.append(CustomError(["query_param","label"], ValueError("invalid entry for commodity")))  
    if(error_list):
        raise PermissionDeniedError(error_list) 
    try:
        label_value = label
        redis_key = f"{pdesk_feature_list_redis_prefix}_imp_table_{date_key}_{label_value}_{lookahead}"
        feature_importance = get_cache(redis_key)
        if(not feature_importance):
            feature_importance = get_feature_importance(label_value,lookahead)
            set_cache((redis_key),feature_importance,expiry_time=settings.time_to_expire)
        return feature_importance
    except Exception as e:
        print(e)
        error_list.append(CustomError(error_loc=["internal_server"],error_object=Exception("Not able to generate table for feature importance")))
        raise InternalServerError(error_list)

@router.get("/explainability/y-variables", status_code=200, response_model=List[DropDownModel])
def fetch_y_variable(*, request: Request, db: Session = Depends(deps.get_db)) -> Any:
    """
    Dropdown Values for Y-variable(commodity)
    """
    dropDownList: List[DropDownModel] = filter_subscribed_commodities(
        request=request, y_variable=y_variable, db=db) 
    return dropDownList


@router.get("/explainability/lookahead-days", status_code=200, response_model=List[DropDownModel])
def fetch_lookahead(*, request: Request, db: Session = Depends(deps.get_db)) -> Any:
    """
    Dropdown Values for lookahead days
    """
    lookahead_days = filter_subscribed_lookahead_Days(
        request=request, lookahead_days=explainability_lookahead_days_list, db=db)
    dropDownList = common.dropDownFormatter(input_list=lookahead_days)
    return dropDownList


@router.get("/importance/explainability/chart", status_code=200, response_model=FinalChartData, response_model_exclude_unset=True, dependencies=[Depends(PermissionChecker(module=ModulesEnum.FEATURE_IMPORTANCE.name,permission=PermissionsEnum.VIEW.name))])
def fetch_feature_importance_chart(*,
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    lookahead: int = Query(15),
    request: Request, db: Session = Depends(deps.get_db)) ->Any:
    """
    Get chart data for feature importance
    """
    date_key = common.today_date_key()
    error_list = []
    if(lookahead not in filter_subscribed_lookahead_Days(request=request, lookahead_days=explainability_lookahead_days_list, db=db)):
        error_list.append(CustomError(["query_param","lookahead"],ValueError("invalid entry for lookahead days"))) 
    if(label not in [y["value"] for y in filter_subscribed_commodities(request=request, y_variable=y_variable, db=db)]):
        error_list.append(CustomError(["query_param","label"], ValueError("invalid entry for commodity")))  
    if(error_list):
        raise PermissionDeniedError(error_list) 
    try:
        is_internal: bool = False
        label_value= label
        redis_key = f"{pdesk_feature_list_redis_prefix}_imp_exp_chart_{date_key}_{label_value}_{lookahead}"
        chart_data = get_cache(redis_key)
        if(not chart_data):
            chart_data = get_explainable_graph_data(label_value,lookahead,is_internal)
            set_cache(redis_key,chart_data,expiry_time=settings.time_to_expire)
        return chart_data
    except Exception as e:
        print(e)
        error_list.append(CustomError(error_loc=["internal_server"],error_object=Exception("Not able to generate chart for importance explainability")))
        raise InternalServerError(error_list)


@router.get("/importance/explainability/all/chart", status_code=200, response_model=FinalChartData, response_model_exclude_unset=True, dependencies=[Depends(PermissionChecker(module=ModulesEnum.FEATURE_IMPORTANCE.name,permission=PermissionsEnum.VIEW.name))])
def fetch_feature_importance_chart_admin(*,
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    lookahead: int = Query(15),
    request: Request, db: Session = Depends(deps.get_db)) ->Any:
    """
    Get chart data for feature importance for admin
    """
    date_key = common.today_date_key()
    
    error_list = []
    if(lookahead not in filter_subscribed_lookahead_Days(request=request, lookahead_days=explainability_lookahead_days_list, db=db)):
        error_list.append(CustomError(["query_param","lookahead"],ValueError("invalid entry for lookahead days"))) 
    if(label not in [y["value"] for y in filter_subscribed_commodities(request=request, y_variable=y_variable, db=db)]):
        error_list.append(CustomError(["query_param","label"], ValueError("invalid entry for commodity")))  
    if(error_list):
        raise PermissionDeniedError(error_list) 
    try:
        is_internal: bool = True
        label_value= label
        redis_key = f"{pdesk_feature_list_redis_prefix}_imp_exp_chart_admin_{date_key}_{label_value}_{lookahead}"
        chart_data = get_cache(redis_key)
        if(not chart_data):
            chart_data = get_explainable_graph_data(label_value,lookahead,is_internal)
            set_cache(redis_key,chart_data,expiry_time=settings.time_to_expire)

        return chart_data
    except Exception as e:
        print(e)
        error_list.append(CustomError(error_loc=["internal_server"],error_object=Exception("Not able to generate chart for importance explainability")))
        raise InternalServerError(error_list)
