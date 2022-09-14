import imp
from fastapi import status, APIRouter, HTTPException, Depends
from passlib.context import CryptContext
from app.api.deps import get_db
from sqlalchemy.orm import Session
from datetime import timedelta, date
from app import crud
from app.schemas.auth import LoginSchema
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.models.user import User
router = APIRouter()


@router.post('/login', status_code=(status.HTTP_201_CREATED))
def login(login_schema: LoginSchema, db: Session = Depends(get_db)):
    """
    Pass username and password it will return the jwt token
    """
    user: User = crud.user.get_by_email(db, email=login_schema.email)
    if not user:
        raise HTTPException(status_code=(status.HTTP_404_NOT_FOUND),
                            detail='User does not exist.')

    is_password_valid = verify_password(login_schema.password, user.password)
    if not is_password_valid:
        raise HTTPException(status_code=(status.HTTP_409_CONFLICT),
                            detail='Please check username and password.')
    if user.status != 1:
        raise HTTPException(status_code=(status.HTTP_401_UNAUTHORIZED),
                            detail='Your account is deactivated.')

    # if not user.is_super_admin:
        # subscriber = crud.crud_subscriber.subscriber.get_by_user(db, user.id)
        # if not subscriber:
        #     raise HTTPException(status_code=(status.HTTP_401_UNAUTHORIZED),
        #                         detail='Please update your company.')
        # is_user_expired = subscriber.expiry_date < date.today()
        # if is_user_expired:
        #     raise HTTPException(status_code=(status.HTTP_401_UNAUTHORIZED),
        #                         detail='Please upgrade your plan.')

    # TODO: need to write the code for the normal user check
    claim = {'email': user.email, 'id': user.id, 'is_super_admin': user.is_super_admin}
    token = create_access_token(claim, expires_delta=timedelta(
        minutes=(settings.ACCESS_TOKEN_EXPIRE_MINUTES)))
    return {'token': token}
