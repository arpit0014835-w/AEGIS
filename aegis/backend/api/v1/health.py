""" 
AEGIS — Health Check Endpoints 
================================	
Liveness and readiness probes for container orchestration.	
""" 

from __future__ import annotations 

from fastapi import APIRouter	

from api.deps import RedisDep	

router = APIRouter() 


@router.get("/health", summary="Health check") 
async def health_check(redis: RedisDep) -> dict:	
    """	
    Returns service health status.	

    - **status**: overall health 
    - **redis**: Redis connectivity 
    """ 
    redis_ok = False 
    try: 
        redis_ok = await redis.ping()	
    except Exception:	
        pass 

    return { 
        "status": "healthy" if redis_ok else "degraded",	
        "service": "aegis-backend",	
        "version": "1.0.0", 
        "components": { 
            "redis": "connected" if redis_ok else "disconnected",	
        },	
    }	
