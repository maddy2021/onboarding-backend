from pydantic import BaseModel, ValidationError, create_model
from pydantic.error_wrappers import ErrorWrapper
from typing import Any, Dict, Optional, Sequence, Type
from pydantic.error_wrappers import ErrorList

# Error Types
INTERNAL_SERVER_ERROR = "InternalServer" 
BAD_REQUEST_ERROR = "Request"
AUTHORIZATION_ERROR = "Authorization"
FORBIDDEN_ERROR = "Permission"

BadRequestErrorModel: Type[BaseModel] = create_model(BAD_REQUEST_ERROR)
ServerErrorModel: Type[BaseModel] = create_model(INTERNAL_SERVER_ERROR)
AuthorizationErrorModel: Type[BaseModel] = create_model(AUTHORIZATION_ERROR)
PermissionErrorModel: Type[BaseModel] = create_model(FORBIDDEN_ERROR)

def create_error_obj_list(error_list):
    return [ErrorWrapper(error_element.error_object,loc=error_element.error_loc) for error_element in error_list]

class CustomError():
    def __init__(self,error_loc=[], error_object=Exception("Error Occured")) -> None:
        self.error_loc = error_loc
        self.error_object= error_object

class BadRequestError(ValidationError):
    def __init__(self,errors: Sequence[CustomError], *, body: Any = None) -> None:
        self.body = body
        self.error_list = create_error_obj_list(errors)
        super().__init__(self.error_list, BadRequestErrorModel)

class InternalServerError(ValidationError):
    def __init__(self, errors: Sequence[CustomError], *, body: Any = None) -> None:
        self.body = body
        self.error_list = create_error_obj_list(errors)
        super().__init__(self.error_list, ServerErrorModel)

class AutherizationError(ValidationError):
    def __init__(self, errors: Sequence[CustomError], *, body: Any = None) -> None:
        self.body = body
        self.error_list = create_error_obj_list(errors)
        super().__init__(self.error_list, AuthorizationErrorModel)

class PermissionDeniedError(ValidationError):
    def __init__(self, errors: Sequence[CustomError], *, body: Any = None) -> None:
        self.body = body
        self.error_list = create_error_obj_list(errors)
        super().__init__(self.error_list, PermissionErrorModel)
