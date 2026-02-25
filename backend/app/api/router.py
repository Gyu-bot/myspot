"""API router registration."""

from fastapi import APIRouter, Depends

from app.api.v1 import notes, places, sources, tags, visits
from app.auth.api_key import verify_api_key

v1_router = APIRouter(prefix="/api/v1", dependencies=[Depends(verify_api_key)])
v1_router.include_router(places.router)
v1_router.include_router(sources.router)
v1_router.include_router(notes.router)
v1_router.include_router(visits.router)
v1_router.include_router(tags.router)
