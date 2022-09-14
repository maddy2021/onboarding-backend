from linecache import cache
from typing import Any, List
from fastapi import APIRouter, Depends, Request ,HTTPException
import redis
from sqlalchemy import null
from app.api import deps
from app.core.cache import delete_cache, delete_cache_by_prefix, get_all_cache, remove_all_cache
from app import crud
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/all",status_code=201)
def get_cache() -> Any:
    result = get_all_cache()      
    return result  

@router.get("/remove/all",status_code=201)
def remove_cache() -> Any:

    result = remove_all_cache()      
    return result  

@router.get("/remove/{cache_key}" , status_code=201)
def remove_cache_by_key(
    *,
    cache_key : str,
) -> Any:

    result = delete_cache(cache_key)
    if result is None:
        raise HTTPException(
            status_code=404, detail=f"cache key {cache_key} not found "
        )
    return result
    
@router.get("/remove_pref/{cache_prefix}" , status_code=201)
def remove_by_prefix(
    *,
    cache_prefix: str,
) -> Any:
    
    result = delete_cache_by_prefix(cache_prefix)
    if result is None:
        raise HTTPException(
            status_code=404, detail=f"cache prefix not start from {cache_prefix}"
        )
    return result