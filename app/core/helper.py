from typing import List, Tuple
from fastapi import Depends, Request
from app import crud
from app.api import deps
from app.schemas.charts import DropDownModel
from app.schemas.user import User, UserSubscriptionData
from app.util.user_util import get_current_user
from sqlalchemy.orm import Session

def filter_subscribed_commodities(request:Request, y_variable, db)->List[DropDownModel]:
    current_user: User = get_current_user(request)
    subscriber_data: UserSubscriptionData = crud.user.get_subscriber_data(db,current_user.id)
    commodities = y_variable
    if(not current_user.is_super_admin):
        commodities = [commodity for commodity in y_variable for value in commodity["commodity"] if value in subscriber_data.commodity]
    return commodities

def filter_subscribed_lookahead_Days(request:Request ,lookahead_days, db)-> List[int]:
    current_user: User = get_current_user(request)
    subscriber_data: UserSubscriptionData = crud.user.get_subscriber_data(db,current_user.id)
    if(not current_user.is_super_admin):
        lookahead_days = [lookahead_day  for lookahead_day in lookahead_days if lookahead_day in subscriber_data.lookahead_days]
    return lookahead_days