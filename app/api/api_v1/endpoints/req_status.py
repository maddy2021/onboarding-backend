from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Any, List
from app import crud
from app.api import deps

from app.schemas.request_status import RequestStatus
from app.schemas.user import User
from app.util.user_util import get_current_user

router = APIRouter()

@router.get("/getall", status_code=200, response_model=List[RequestStatus])
def fetch_all_requests(
    *,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch all status_data
    """
    status_data = crud.req_status.get_multi(db=db)
    if not status_data:
        return []
    return status_data

