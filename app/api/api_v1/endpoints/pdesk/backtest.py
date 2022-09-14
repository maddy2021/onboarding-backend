import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Any, List

from app import crud
import app
from app.CustomErrors.HTTPErrors.http_base_error import BadRequestError, CustomError, InternalServerError, PermissionDeniedError
from app.api import deps
from app.core.cache import get_cache, set_cache
from app.core.config import settings
from sqlalchemy.orm import Session
from app.core.helper import filter_subscribed_commodities, filter_subscribed_lookahead_Days
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.helpers.pdesk.backtest.directional_correctness_helper import box_plot_data, plotting_metric_dir_corr
from app.helpers.pdesk.backtest.scalable_model_helper import get_scalable_model_df
from app.schemas.charts import DropDownModel
from app.schemas.pdesk import FinalChartData, ScatterChart, BarChart, BoxChart
from app.schemas.user import User, UserSubscriptionData
from app.util import common
from app.util.user_util import get_current_user


router = APIRouter()

# Load static data from template regarding backtest model api
pdesk_template = settings.template_data["pdesk"]["backtest"]
y_variable = pdesk_template["y_variable"]
lookahead_days_list = pdesk_template["lookahead_admin"]
model_type = pdesk_template["model_type"]
percentage_list = pdesk_template["percentage_list"]
pdesk_backtest_redis_prefix = "pdesk_bt" 


@router.get("/y-variables", status_code=200, response_model=List[DropDownModel])
def fetch_y_variable(*, request: Request, db: Session = Depends(deps.get_db)) -> Any:
    """
    Dropdown Values for Y-variable(commodity)
    """
    dropDownList: List[DropDownModel] = filter_subscribed_commodities(
        request=request, y_variable=y_variable, db=db)
    return dropDownList


@router.get("/lookahead-days", status_code=200, response_model=List[DropDownModel])
def fetch_lookahead(*, request: Request, db: Session = Depends(deps.get_db)) -> Any:
    """
    Dropdown Values for lookahead days
    """
    lookahead_days = filter_subscribed_lookahead_Days(
        request=request, lookahead_days=lookahead_days_list, db=db)
    dropDownList = common.dropDownFormatter(input_list=lookahead_days)
    return dropDownList


@router.get("/high-impact-percentages", status_code=200, response_model=List[DropDownModel])
def fetch_percentage() -> Any:
    """
    Dropdown Values for percentage 
    """
    dropDownList = common.dropDownFormatter(input_list=percentage_list, extra_tag="%")
    return dropDownList


@router.get("/scalable_model/chart", status_code=200, response_model=FinalChartData, response_model_exclude_unset=True, dependencies=[Depends(PermissionChecker(module=ModulesEnum.BACKTEST.name,permission=PermissionsEnum.VIEW.name))])
def fetch_scalable_chart(
    *,
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    lookahead: int = Query(15),
    request: Request, db: Session = Depends(deps.get_db)
):
    """
    Get chart data for backtest scalable model
    """
    error_list = []
    date_key = common.today_date_key()
    if(lookahead not in filter_subscribed_lookahead_Days(request=request, lookahead_days=lookahead_days_list, db=db)):
        error_list.append(CustomError(["query_param","lookahead"],ValueError("invalid entry for lookahead days")))
    if(label not in [y["value"] for y in filter_subscribed_commodities(request=request, y_variable=y_variable, db=db)]):
        error_list.append(CustomError(["query_param","label"], ValueError("invalid entry for commodity")))    
    if(error_list):
        raise PermissionDeniedError(error_list)
    try:
        lookahead_value = lookahead
        label_value = label
        label_name = ""
        for data in y_variable:
            if(data["value"] == label_value):
                label_name = data["label"]
                break
        redis_key = f"{pdesk_backtest_redis_prefix}_sc_chart_{date_key}_{label_value}_{lookahead}"
        graph_data = get_cache(redis_key)
        if(not graph_data):
            graph_data: FinalChartData = get_scalable_model_df(
                label_value=label_value, model_type=model_type, lookahead_value=lookahead_value, label_name=label_name)
            set_cache(redis_key,graph_data,expiry_time=settings.time_to_expire)
  
        return graph_data
    except Exception as e:
        print(e)
        error_list.append(CustomError(error_loc=["internal_server"],error_object=Exception("Not able to generate scalable model chart for backtest")))
        raise InternalServerError(error_list)

@router.get("/complete-history/directional-correctness/chart", status_code=200, response_model=FinalChartData, response_model_exclude_unset=True, dependencies=[Depends(PermissionChecker(module=ModulesEnum.COMPLETE_HISTORY_BACKTEST_METRIC.name,permission=PermissionsEnum.VIEW.name))])
def fetch_correctness_history_chart(
    *,
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    high_impact_percentages: int = Query(3),
    request: Request, db: Session = Depends(deps.get_db)
):
    """
    Get chart data for backtest complete history model (correctness)
    """
    error_list = []
    date_key = common.today_date_key()
    
    if(high_impact_percentages not in percentage_list):
        error_list.append(CustomError(["query_param","high_impact_perentages"],ValueError("invalid entry for high_impact_perentages")))   
    if(label not in [y["value"] for y in filter_subscribed_commodities(request=request, y_variable=y_variable, db=db)]):
        error_list.append(CustomError(["query_param","label"],ValueError("invalid entry for commodity")))   
    if error_list:
        raise PermissionDeniedError(error_list)
    try:
        percentage = high_impact_percentages
        label_value = label
        redis_key = f"{pdesk_backtest_redis_prefix}_ch_dc_chart_{date_key}_{label_value}_{percentage}"
        graph_data = get_cache(redis_key)
        if(not graph_data):
            graph_data = plotting_metric_dir_corr(
                y_variable=label_value, model_type=model_type, val_per=percentage)
            set_cache(redis_key,graph_data,expiry_time=settings.time_to_expire)
        return graph_data
    except Exception as e:
        print(e)
        error_list.append(CustomError(["internal_server"],Exception("Error while generate directional correctness chart for backtest")))
        raise InternalServerError(error_list)



@router.get("/complete-history/absolute-delta/chart", status_code=200, response_model=FinalChartData, response_model_exclude_unset=True)
def fetch_absolute_delta_chart(
    *,
    label: str = Query("3_cpo_bmd_prices_USD_per_MT"),
    request: Request, db: Session = Depends(deps.get_db)
):
    """
    Get chart data for backtest complete history model (absolute_delta)
    """
    date_key = common.today_date_key()
    
    if(label not in [y["value"] for y in filter_subscribed_commodities(request=request, y_variable=y_variable, db=db)]):
        raise PermissionDeniedError([CustomError(["query_param","label"],Exception("invalid entry for commodity"))])
    try:
        label_value = label
        redis_key = f"{pdesk_backtest_redis_prefix}_ch_ad_chart_{date_key}_{label_value}"
        graph_data = get_cache(redis_key)
        if(not graph_data):
            graph_data = box_plot_data(y_variable=label_value, model_type=model_type)
            set_cache(redis_key,graph_data,expiry_time=settings.time_to_expire)
        return graph_data
    except Exception as e:
        print(e)
        raise InternalServerError([CustomError(["internal_server"],Exception("Error while generate absolute delta chart for backtest"))])
