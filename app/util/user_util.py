from fastapi.requests import Request

from app.schemas.user import UserCacheSchema
from typing import List


def get_current_user(request: Request):
    return request.state.current_user


def get_current_user_permission(request: Request) -> List[str]:
    return request.state.permissions
