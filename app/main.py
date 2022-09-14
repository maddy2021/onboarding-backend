import json
from pathlib import Path
import sys
import traceback

from fastapi import FastAPI, APIRouter, Request, Response, status
from app.CustomErrors.HTTPErrors.http_base_error import AutherizationError, BadRequestError, CustomError, InternalServerError, PermissionDeniedError
from app.api.api_v1.api import api_router
from app.core.config import settings
from app.middleware.auth_middleware import AuthMiddleWare
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.routing import APIRoute
from typing import Callable

BASE_PATH = Path(__file__).resolve().parent
# TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates"))

# Reference https://stackoverflow.com/questions/61596911/catch-exception-in-fast-api-globally 
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        ex_type, ex, tb = sys.exc_info()
        print(e.with_traceback(tb))
        print(traceback.format_exc())
        if isinstance(e, BadRequestError):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail":json.loads(e.json())})
        elif isinstance(e, InternalServerError):
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail":json.loads(e.json())})
        elif isinstance(e, AutherizationError):
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail":json.loads(e.json())})
        elif isinstance(e, PermissionDeniedError):
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail":json.loads(e.json())})
        else:
            exception_ = InternalServerError(errors=[CustomError(error_loc=["internal_server"],error_object=Exception("Some error occured. Contact to admin"))])
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail":json.loads(exception_.json())})
        # return Response("Internal server error", status_code=500)

app = FastAPI(title="Onboarding API")

# DO NOT CHANAGE the position of the middleware
# app.add_middleware(PermissionMiddleware)
app.add_middleware(AuthMiddleWare)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],)
app.middleware('http')(catch_exceptions_middleware)

app.include_router(api_router, prefix=settings.API_V1_STR)
root_router = APIRouter()
app.include_router(root_router)


if __name__ == "__main__":
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug")
