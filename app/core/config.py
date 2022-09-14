from pydantic import AnyHttpUrl, BaseSettings, EmailStr, validator
from typing import List, Optional, Union
import pathlib
import os

from app.util import common

file_parent_directory = pathlib.Path(__file__).parent.parent.resolve()
template_file_path = os.path.join(file_parent_directory,"assets","kt_links.json")
print(template_file_path)


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    FIRST_SUPERUSER: EmailStr = "admin@capgemini.com"
    SECRET_KEY: str = "secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    SQLALCHEMY_DATABASE_URI: str = "postgresql://postgres:password@localhost:5432/test-db2"
    # SQLALCHEMY_CRUDE_PALM_OIL_URI: str = "postgresql://aifund:qwerty123@crudepalmoildata.ccv7u2kjouwe.us-east-2.rds.amazonaws.com:5432/CrudePalmOilData"

    # REDIS_HOST: str = "localhost"
    # REDIS_PORT: int = 6379
    DATA_FILE_PATH = os.path.join(file_parent_directory,"data")
    template_data = common.read_json_file(template_file_path)
    time_to_expire = 86400  # 24 hours = 86400 seconds

    class Config:
        case_sensitive = True
        env_file = '.env'


settings = Settings()
