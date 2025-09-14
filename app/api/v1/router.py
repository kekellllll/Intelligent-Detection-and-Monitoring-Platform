"""Main API router."""
from fastapi import APIRouter

from app.api.v1.sensors import router as sensors_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.graphql_api import graphql_app

api_router = APIRouter()

# Include sub-routers
api_router.include_router(sensors_router)
api_router.include_router(monitoring_router)

# Mount GraphQL app
api_router.mount("/graphql", graphql_app)