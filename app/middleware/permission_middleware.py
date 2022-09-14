# import json
# from fastapi.requests import Request
# from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
# from app.core.security import is_unauthorized_url
# from app.db.session import SessionLocal
# from app.schemas.user import UserCacheSchema
# from app.util.json_encode_util import authentication_fail_json
# from app.crud import crud_user
# from app.core.cache import cache_obj
# from inspect import signature


# class PermissionMiddleware(BaseHTTPMiddleware):

#     async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
#         if is_unauthorized_url(request):
#             return await call_next(request)

#         user_schema: UserCacheSchema = request.state.current_user
#         if user_schema.is_super_admin:
#             return await call_next(request)

#         db = None
#         cache_key = "per_" + str(user_schema.id)
#         try:
#             db = SessionLocal()
#             permission_str = cache_obj.get(cache_key)
#             if not permission_str:
#                 user = crud_user.user.get_by_email(db=db, email=user_schema.email)
#                 if not user:
#                     return authentication_fail_json("Please check authentication token.")

#                 result = crud_user.user.get_all_user_permissions(db, user)
#                 permissions = [r[0] for r in result]
#                 cache_obj.set(cache_key, json.dumps(permissions))
#                 permission_str = cache_obj.get(cache_key)

#             permissions = json.loads(permission_str)
#             request.state.permissions = permissions
#         except Exception as e:
#             print(str(e))
#             return authentication_fail_json("Please check authentication token.")
#         finally:
#             if db != None:
#                 db.close()

#         return await call_next(request)
