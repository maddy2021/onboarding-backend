from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Any, List
from app import crud
from app.api import deps

from app.schemas.module import ModuleCreate, Module, ModuleUpdate
from app.schemas.user import User
from app.util.user_util import get_current_user

router = APIRouter()


@router.get("/getById/{module_id}", status_code=200, response_model=Module)
def fetch_module(
    *,
    module_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch a single module by ID
    """
    result = crud.permission.get(db=db, id=module_id)
    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        return {}

    return result

@router.get("/getall", status_code=200, response_model=List[Module])
def fetch_all_module(
    *,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch all modules
    """
    modules = crud.module.get_multi(db=db)
    if not modules:
        return []
    return modules

@router.post("/update", status_code=201, response_model=Module)
def update_module(
    *, request:Request,module_in: ModuleUpdate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Update a new module in the database.
    provide fields which need to be updtaed and id is must needed
    """
    current_user: User = get_current_user(request)
    modified_by = current_user.id 
    result = crud.module.get(db=db, id=module_in.id)
    module = crud.module.update(db=db,db_obj=result ,obj_in=module_in,modified_by=modified_by)
    
    return module

# @router.get("/search/", status_code=200, response_model=RecipeSearchResults)
# def search_recipes(
#     *,
#     keyword: Optional[str] = Query(None, min_length=3, example="chicken"),
#     max_results: Optional[int] = 10,
#     db: Session = Depends(deps.get_db),
# ) -> dict:
#     """
#     Search for recipes based on label keyword
#     """
#     recipes = crud.recipe.get_multi(db=db, limit=max_results)
#     if not keyword:
#         return {"results": recipes}

#     results = filter(lambda recipe: keyword.lower() in recipe.label.lower(), recipes)
#     return {"results": list(results)[:max_results]}


@router.post("/", status_code=201, response_model=Module)
def create_module(
    *, request: Request,module_in: ModuleCreate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Create a new module in the database.
    """
    current_user: User = get_current_user(request)
    created_by = current_user.id 
    # user_in.expiry_date = parser.parse(user_in.expiry_date)
    role = crud.module.create(db=db, obj_in=module_in,created_by=created_by)
    return role
