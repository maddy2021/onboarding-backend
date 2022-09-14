from fastapi import status
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.session import SessionLocal
from app.core.security import decode_access_token, is_unauthorized_url
from app import crud
from app.core.cache import cache_obj
import json

from app.schemas.user import UserCacheSchema
from app.util.json_encode_util import authentication_fail_json


class AuthMiddleWare(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        if is_unauthorized_url(request):
            return await call_next(request)
        token = request.headers.get('Authorization', None)
        if token == None:
            return authentication_fail_json("Authentication header missing")
        claim = decode_access_token(token)
        if claim == None:
            return authentication_fail_json("Please check authentication token.")
        id = claim.get('id', None)
        if id == None:
            return authentication_fail_json("Please check authentication token.")
        db = None
        try:
            db = SessionLocal()
            # cache_key = id
            # cache_user_str = cache_obj.get(cache_key)
            # if not cache_user_str:
            user = crud.user.get_by_id(db, id=id)
            if not user:
                return authentication_fail_json("User not found.")
                # cache_obj.set(cache_key, json.dumps(user.toJson()))
                # cache_user_str = cache_obj.get(cache_key)
            # cache_user = json.loads(cache_user_str)
            # userCacheSchema = UserCacheSchema(**cache_user)
            # request.state.current_user = userCacheSchema
            request.state.current_user = user  
        except Exception as e:
            print(str(e))
            return authentication_fail_json("Got expception from fetching data.")
        finally:
            if db != None:
                db.close()
        return await call_next(request)
