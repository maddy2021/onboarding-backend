from typing import Optional
from fastapi import Depends
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.core.config import settings
from jose import jwt
from fastapi.security import HTTPBearer
from fastapi.requests import Request
from functools import wraps

reusable_oauth2 = HTTPBearer(
    scheme_name='Authorization'
)
PREFIX = 'Bearer'


password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_context.hash(password)


def create_access_token(claim: dict, expires_delta: Optional[timedelta] = None):
    to_encode = claim.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({'exp': expire})
    jwt_token = jwt.encode(to_encode, settings.SECRET_KEY, settings.ALGORITHM)
    return jwt_token


def decode_access_token(token):
    payload = None
    try:
        auth_token = get_token(token)
        payload = jwt.decode(auth_token, settings.SECRET_KEY, settings.ALGORITHM)
    except Exception as e:
        print('Problem with token decode => ', str(e))
    return payload


def get_token(header):
    bearer, _, token = header.partition(' ')
    if bearer != PREFIX:
        raise ValueError('Invalid token')

    return token


def is_unauthorized_url(request: Request):
    allow_urls = ['/docs', '/openapi.json', '/api/v1/auth/login', "/"]
    current_url = request.url.path
    if current_url in allow_urls:
        return True
    return False


def has_permissions(permissions: list, request: Request = Depends()):
    print(permissions)
    return True
