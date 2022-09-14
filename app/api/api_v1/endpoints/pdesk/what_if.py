from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from typing import Any, List
from app.CustomErrors.HTTPErrors.http_base_error import BadRequestError, CustomError, InternalServerError, PermissionDeniedError
from app.api import deps
from app.core.config import settings
from app.core.helper import filter_subscribed_commodities
from app.core.permission_checker import ModulesEnum, PermissionChecker, PermissionsEnum
from app.helpers.pdesk.backtest.what_if_helper import calculate_what_if, input_parameter_list
from app.schemas.charts import DropDownModel
from app.schemas.pdesk import FinalChartData
from app.schemas.user import UserCreate
from app.util import common
from sqlalchemy.orm import Session

router = APIRouter()

what_if_template = settings.template_data["pdesk"]["what_if"]
y_variable = what_if_template["y_variable"]
feature_dict = what_if_template["features"]
weighted_features_dict = what_if_template["weighted_features"]
# ft_list_3 = weighted_features_list["ft_list_3"]
# ft_list_2 = weighted_features_list["ft_list_2"]
# ft_list_1 = weighted_features_list["ft_list_1"]


@router.get("/y-variables", status_code=200, response_model=List[DropDownModel])
def fetch_y_variable(*, request: Request, db: Session = Depends(deps.get_db)) -> Any:
    """
    Dropdown Values for Y-variable(commodity)
    """
    dropDownList: List[DropDownModel] = filter_subscribed_commodities(
        request=request, y_variable=y_variable, db=db)
    return dropDownList


@router.get("/{y_var}/input_features", status_code=200)
def fetch_y_variable(*,y_var: str,request: Request, admin_db: Session = Depends(deps.get_db)) -> Any:
    """
    input feature for the given commodity
    """
    if(y_var not in [y["value"] for y in  filter_subscribed_commodities(request=request, y_variable=y_variable, db=admin_db)]):
        raise PermissionDeniedError([CustomError(["query_param","label"], ValueError("invalid entry for commodity"))])       
    start_year = 2014
    input_list = feature_dict[y_var]
    _,_,input_feature_dict,_=input_parameter_list(y_var, start_year, input_list)
    return input_feature_dict


@router.post("/{y_var}/chart/",response_model=FinalChartData,response_model_exclude_unset=True,dependencies=[Depends(PermissionChecker(module=ModulesEnum.WHAT_IF.name,permission=PermissionsEnum.VIEW.name))])
def fetch_chart(
    *,request:Request,y_var: str, body_in: dict = Body(...),
    admin_db: Session = Depends(deps.get_db)
) -> Any:
    """
    get what-if chart data
    """
    if(y_var not in [y["value"] for y in  filter_subscribed_commodities(request=request, y_variable=y_variable, db=admin_db)]):
        raise PermissionDeniedError([CustomError(["path_param","label"], ValueError("invalid entry for commodity in path"))])  
    input_list = feature_dict[y_var]
    input_dict = body_in
    if(set(input_list)-set(input_dict.keys())):
        raise BadRequestError([CustomError(["body_in","data"], ValueError("invalid data in request body"))])
    start_year = 2014
    label_name = ""
    label_code = ""
    for data in y_variable:
        if(data["value"]==y_var):
            label_name = data["label"]
            label_code = data["code"]
            break
    try:
        input_feature_dict=calculate_what_if(y_var, input_list, input_dict, start_year, label_code, weighted_features_dict)
        return input_feature_dict
    except Exception as e:
        raise e
        # raise InternalServerError([CustomError(error_loc=["internal_server"],error_object=Exception("Not able to generate chart for what-if"))])
