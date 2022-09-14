from fastapi.responses import JSONResponse
from fastapi import status, HTTPException


def json_response(message: str, status_code: str):
    return JSONResponse(content={'detail': message}, status_code=status_code)


def authentication_fail_json(message: str):
    return json_response(message, status.HTTP_401_UNAUTHORIZED)


def raise_http_exception(message: str, stats_code: str):
    return HTTPException(status_code=stats_code, detail=message)


def authorization_fail(message: str):
    return raise_http_exception(message, status.HTTP_401_UNAUTHORIZED)
