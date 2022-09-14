# from fastapi import APIRouter, Depends
# from app.core.security import reusable_oauth2
# from app.api.api_v1.endpoints.pdesk import backtest, basis_risk, feature_list, historical_volatility, inference, public_posting, what_if

# router = APIRouter()

# # Routes Regarding Pdesk, What you provide in tags will used as title in openapi docs
# router.include_router(backtest.router, prefix="/backtest",tags=["backtest"],dependencies=[Depends(reusable_oauth2)])
# router.include_router(feature_list.router, prefix="/features",tags=["features"],dependencies=[Depends(reusable_oauth2)])
# router.include_router(inference.router, prefix="/inference",tags=["inference"],dependencies=[Depends(reusable_oauth2)])
# router.include_router(historical_volatility.router, prefix="/historical",tags=["historical"],dependencies=[Depends(reusable_oauth2)])
# router.include_router(basis_risk.router, prefix="/basis-risk",tags=["basis-risk"],dependencies=[Depends(reusable_oauth2)])
# router.include_router(public_posting.router, prefix="/public-posting",tags=["public-posting"],dependencies=[Depends(reusable_oauth2)])
# router.include_router(what_if.router, prefix="/what-if",tags=["what-if"],dependencies=[Depends(reusable_oauth2)])
