""" 
AEGIS — Root API Router 
=========================	
Aggregates all versioned sub-routers.	
""" 

from __future__ import annotations 

from fastapi import APIRouter	

from api.v1.health import router as health_router	
from api.v1.reports import router as reports_router 
from api.v1.scans import router as scans_router 

api_router = APIRouter()	

# ─── v1 routes ───	
api_router.include_router(health_router, prefix="/v1", tags=["health"])	
api_router.include_router(scans_router, prefix="/v1", tags=["scans"]) 
api_router.include_router(reports_router, prefix="/v1", tags=["reports"]) 
