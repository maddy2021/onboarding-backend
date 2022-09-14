from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Any, List
from app.CustomErrors.HTTPErrors.http_base_error import CustomError, InternalServerError, PermissionDeniedError
from app.api import deps
from app.core.cache import get_cache, set_cache
from app.core.config import settings
from app.core.helper import filter_subscribed_commodities
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.helpers.pdesk.backtest.public_posting_helper import get_absolute_delta_graph, get_dependent_values, get_directional_correctness_graph
from app.helpers.pdesk.backtest.public_posting_helper_for_month import get_predicted_absolute_delta_graph, get_predicted_directional_correctness_graph
from app.schemas.charts import DropDownModel
from app.schemas.pdesk import FinalChartData
from app.util import common
from sqlalchemy.orm import Session

router = APIRouter()

public_posting_template = settings.template_data["pdesk"]["public_posting"]
y_variable = public_posting_template["y_variable"]
high_impact_cases = public_posting_template["high_impact_cases"]
months_dict = public_posting_template["months_mapping"]
model_type = public_posting_template["model_type"]
pdesk_pub_post_prefix = "pdesk_pub_post"


@router.get("/y-variables", status_code=200, response_model=List[DropDownModel])
def fetch_y_variable(*,request: Request, db: Session = Depends(deps.get_db)) -> Any:
    """
    Dropdown Values for Y-variable(commodity)
    """
    dropDownList: List[DropDownModel] = filter_subscribed_commodities(
        request=request, y_variable=y_variable, db=db)
    return dropDownList

@router.get("/y-variable/month-year-impact", status_code=200)
def fetch_dependent_valuess( *,
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    request: Request, db: Session = Depends(deps.get_db)) -> Any:
    """
    Dropdown values for months, years, high impact cases percentage
    """
    date_key = common.today_date_key()
    if(label not in [y["value"] for y in filter_subscribed_commodities(
        request=request, y_variable=y_variable, db=db)]):
        raise PermissionDeniedError([CustomError(["query_param","label"], ValueError("invalid entry for commodity"))])  
    try:
        label_value = label
        redis_key = f"{pdesk_pub_post_prefix}_m_y_i_{date_key}_{label_value}"
        dependent_value_dict = get_cache(redis_key)
        if(not dependent_value_dict):
            dependent_value_dict=get_dependent_values(label_value,high_impact_cases,months_dict)
            for key,list_value in dependent_value_dict.items():
                if(key=="high_impact_cases"):
                    dependent_value_dict[key] = common.dropDownFormatter(list_value,extra_tag="%")
                else:
                    dependent_value_dict[key] = common.dropDownFormatter(list_value)
            set_cache(redis_key,dependent_value_dict,expiry_time=settings.time_to_expire)    
        return dependent_value_dict
    except Exception as e:
        print(e)
        raise InternalServerError([CustomError(error_loc=["internal_server"],error_object=Exception("Not able to get month-year-impact data"))])

@router.get("/month-in-prediction/directional-correctness/chart", status_code=200, response_model=FinalChartData, response_model_exclude_unset=True, dependencies=[Depends(PermissionChecker(module=ModulesEnum.PUBLIC_POSTING_MONTH_IN.name,permission=PermissionsEnum.VIEW.name))])
def fetch_correctness_chart(
    *,
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    high_impact_case: int = Query(0),
    month: str,
    year: str,
    request: Request, db: Session = Depends(deps.get_db)
)->Any:
    """
    Get a directional correctioness chart data
    """
    date_key = common.today_date_key()
    error_list = []
    if(label not in [y["value"] for y in filter_subscribed_commodities(
        request=request, y_variable=y_variable, db=db)]):
        error_list.append([CustomError(["query_param","label"], ValueError("invalid entry for commodity"))]) 
    else:
        dependent_value_dict=get_dependent_values(label,high_impact_cases,months_dict)
        if(month not in dependent_value_dict["months"]):
            error_list.append(CustomError(["query_param","month"], ValueError("invalid entry for month")))
        if(year not in dependent_value_dict["years"]):
            error_list.append(CustomError(["query_param","month"], ValueError("invalid entry for year")))
        if(high_impact_case not in dependent_value_dict["high_impact_cases"]):
            error_list.append(CustomError(["query_param","month"], ValueError("invalid entry for high impact percentage")))
    if(error_list):
        raise PermissionDeniedError(error_list)
    try:
        label_value = label
        label_name = ""
        label_code = ""
        for data in y_variable:
            if(data["value"]==label_value):
                label_name = data["label"]
                label_code = data["code"]
                break
        redis_key = f"{pdesk_pub_post_prefix}_m_in_pred_dc_chart{date_key}_{label_value}_{high_impact_case}_{month}_{year}"
        graph_data = get_cache(redis_key)
        if(not graph_data):
            graph_data = get_directional_correctness_graph(label_value,label_name,month,year,high_impact_case,months_dict,label_code)
            set_cache(redis_key,graph_data,expiry_time=settings.time_to_expire)
        return graph_data
    except Exception as e:
        raise e
    
@router.get("/month-in-prediction/absolute-delta/chart", status_code=200, response_model=FinalChartData, response_model_exclude_unset=True, dependencies=[Depends(PermissionChecker(module=ModulesEnum.PUBLIC_POSTING_MONTH_IN.name,permission=PermissionsEnum.VIEW.name))])
def fetch_permission(
    *,
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    month: str,
    year: str,
    request: Request, db: Session = Depends(deps.get_db)
)->Any:
    """
    Get absolute delta chart data
    """
    date_key = common.today_date_key()
   
    error_list = []
    if(label not in [y["value"] for y in filter_subscribed_commodities(
        request=request, y_variable=y_variable, db=db)]):
        error_list.append([CustomError(["query_param","label"], ValueError("invalid entry for commodity"))]) 
    else:
        dependent_value_dict=get_dependent_values(label,high_impact_cases,months_dict)
        if(month not in dependent_value_dict["months"]):
            error_list.append(CustomError(["query_param","month"], ValueError("invalid entry for month")))
        if(year not in dependent_value_dict["years"]):
            error_list.append(CustomError(["query_param","month"], ValueError("invalid entry for year")))
    if(error_list):
        raise PermissionDeniedError(error_list)
    try: 
        label_value = label
        label_name = ""
        label_code = ""
        for data in y_variable:
            if(data["value"]==label_value):
                label_name = data["label"]
                label_code = data["code"]
                break
        redis_key = f"{pdesk_pub_post_prefix}_m_in_pred_ad_chart{date_key}_{label_value}_{month}_{year}"
        graph_data = get_cache(redis_key)
        if(not graph_data):
            graph_data = get_absolute_delta_graph(label_value,month,year,label_name,months_dict,label_code)
            set_cache(redis_key,graph_data,expiry_time=settings.time_to_expire)
        return graph_data
    except Exception as e:
        print(e)
        error_list.append(CustomError(error_loc=["internal_server"],error_object=Exception("Not able to generate chart for public posting(month-in-prediction, absolute-delta)")))
        raise InternalServerError(error_list)

@router.get("/month-for-prediction/directional-correctness/chart", status_code=200, response_model=FinalChartData, response_model_exclude_unset=True, dependencies=[Depends(PermissionChecker(module=ModulesEnum.PUBLIC_POSTING_MONTH_FOR.name,permission=PermissionsEnum.VIEW.name))])
def fetch_permission(
    *,
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    high_impact_case: int = Query(0),
    month: str,
    year: str,
    request: Request, db: Session = Depends(deps.get_db)
)->Any:
    """
    Get predicted directional correctional chart data
    """
    date_key = common.today_date_key()
   
    error_list = []
    if(label not in [y["value"] for y in filter_subscribed_commodities(
        request=request, y_variable=y_variable, db=db)]):
        error_list.append([CustomError(["query_param","label"], ValueError("invalid entry for commodity"))]) 
    else:
        dependent_value_dict=get_dependent_values(label,high_impact_cases,months_dict)
        if(month not in dependent_value_dict["months"]):
            error_list.append(CustomError(["query_param","month"], ValueError("invalid entry for month")))
        if(year not in dependent_value_dict["years"]):
            error_list.append(CustomError(["query_param","month"], ValueError("invalid entry for year")))
        if(high_impact_case not in dependent_value_dict["high_impact_cases"]):
            error_list.append(CustomError(["query_param","month"], ValueError("invalid entry for high impact percentage")))
    if(error_list):
        raise PermissionDeniedError(error_list)
    try:
        label_value = label
        label_name = ""
        label_code = ""
        for data in y_variable:
            if(data["value"]==label_value):
                label_name = data["label"]
                label_code = data["code"]
                break
        redis_key = f"{pdesk_pub_post_prefix}_m_for_pred_dc_chart{date_key}_{label_value}_{high_impact_case}_{month}_{year}"
        graph_data = get_cache(redis_key)
        if(not graph_data):
            graph_data = get_predicted_directional_correctness_graph(label_value,label_name,month,year,high_impact_case,months_dict,label_code)
            set_cache(redis_key,graph_data,expiry_time=settings.time_to_expire)
        return graph_data
    except Exception as e:
        print(e)
        error_list.append(CustomError(error_loc=["internal_server"],error_object=Exception("Not able to generate chart for public posting(month-for-prediction, directional-correctional)")))
        raise InternalServerError(error_list)

@router.get("/month-for-prediction/absolute-delta/chart", status_code=200, response_model=FinalChartData, response_model_exclude_unset=True, dependencies=[Depends(PermissionChecker(module=ModulesEnum.PUBLIC_POSTING_MONTH_FOR.name,permission=PermissionsEnum.VIEW.name))])
def fetch_permission(
    *,
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    month: str,
    year: str,
    request: Request, db: Session = Depends(deps.get_db)
)->Any:
    """
    Get predicted absolute delta chart data
    """
    date_key = common.today_date_key()
    error_list = []
    if(label not in [y["value"] for y in filter_subscribed_commodities(
        request=request, y_variable=y_variable, db=db)]):
        error_list.append([CustomError(["query_param","label"], ValueError("invalid entry for commodity"))]) 
    else:
        dependent_value_dict=get_dependent_values(label,high_impact_cases,months_dict)
        if(month not in dependent_value_dict["months"]):
            error_list.append(CustomError(["query_param","month"], ValueError("invalid entry for month")))
        if(year not in dependent_value_dict["years"]):
            error_list.append(CustomError(["query_param","month"], ValueError("invalid entry for year")))
    if(error_list):
        raise PermissionDeniedError(error_list)
    try:
        label_value = label
        label_name = ""
        label_code = ""
        for data in y_variable:
            if(data["value"]==label_value):
                label_name = data["label"]
                label_code = data["code"]
                break
        redis_key = f"{pdesk_pub_post_prefix}_m_for_pred_ad_chart{date_key}_{label_value}_{month}_{year}"
        graph_data = get_cache(redis_key)
        if(not graph_data):
            graph_data = get_predicted_absolute_delta_graph(label_value,month,year,label_name,months_dict,label_code)
            set_cache(redis_key,graph_data,expiry_time=settings.time_to_expire)
        return graph_data
    except Exception as e:
        print(e)
        error_list.append(CustomError(error_loc=["internal_server"],error_object=Exception("Not able to generate chart for public posting(month-for-prediction, absolute-delta)")))
        raise InternalServerError(error_list) 
