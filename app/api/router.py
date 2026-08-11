from fastapi import APIRouter

from app.api.endpoints import upload, debts, investments, real_estate, livestock, vehicles, dashboard

api_router = APIRouter()

api_router.include_router(upload.router, tags=["Upload"])
api_router.include_router(debts.router, tags=["Debts"])
api_router.include_router(investments.router, tags=["Investments"])
api_router.include_router(real_estate.router, tags=["Real Estate"])
api_router.include_router(livestock.router, tags=["Livestock"])
api_router.include_router(vehicles.router, tags=["Vehicles"])
api_router.include_router(dashboard.router, tags=["Dashboard"])
