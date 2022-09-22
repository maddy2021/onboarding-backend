from fastapi import APIRouter, Depends

from app.core.security import reusable_oauth2

from app.api.api_v1.endpoints import cache, designations, kt_links, permission, roles, user, auth, module, projects, tools, req_status

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

api_router.include_router(user.router, prefix="/user",
                          tags=["user"],dependencies=[Depends(reusable_oauth2)])

api_router.include_router(tools.router, prefix="/tools",
                          tags=["tools"],dependencies=[Depends(reusable_oauth2)])

api_router.include_router(designations.router, prefix="/designations",
                          tags=["designations"],dependencies=[Depends(reusable_oauth2)])

api_router.include_router(projects.router, prefix="/projects",
                          tags=["projects"],dependencies=[Depends(reusable_oauth2)])

api_router.include_router(roles.router, prefix="/roles",
                          tags=["role"], dependencies=[Depends(reusable_oauth2)])

api_router.include_router(permission.router, prefix="/permission",
                          tags=["permission"], dependencies=[Depends(reusable_oauth2)])

api_router.include_router(kt_links.router, prefix="/kt_links",
                          tags=["kt_links"], dependencies=[Depends(reusable_oauth2)])

api_router.include_router(module.router, prefix="/module",
                          tags=["module"], dependencies=[Depends(reusable_oauth2)])

api_router.include_router(req_status.router, prefix="/req_status",
                          tags=["req_status"], dependencies=[Depends(reusable_oauth2)])


api_router.include_router(cache.router, prefix="/cache",
                          tags=["cache"], dependencies=[Depends(reusable_oauth2)])
