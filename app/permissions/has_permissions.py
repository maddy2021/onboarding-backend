from fastapi.requests import Request
from app.schemas.user import UserCacheSchema
from app.util.json_encode_util import authorization_fail

from app.util.user_util import get_current_user, get_current_user_permission


class HasPermissions:
    def __init__(self, permissions: list):
        self.permissions = permissions

    def __call__(self, request: Request):
        print("Has Permission Dependencies")
        current_user: UserCacheSchema = get_current_user(request)
        if current_user.is_super_admin:
            return

        current_user_permission = get_current_user_permission(request)

        has_permission = True

        for permission in self.permissions:
            has_permission = has_permission and (permission in current_user_permission)

        if not has_permission:
            raise authorization_fail("Does not have privileges")
