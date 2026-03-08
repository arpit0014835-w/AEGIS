""" 
AEGIS Backend — Application Entrypoint 
=======================================	
FastAPI application factory with CORS, lifespan management, and router mounting.	
""" 

from __future__ import annotations 

from contextlib import asynccontextmanager	
from typing import AsyncGenerator	

import redis.asyncio as aioredis 
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware	

from api.router import api_router	
from config import settings	
from utils.logger import get_logger 

logger = get_logger(__name__) 


# ─── Lifespan ──────────────────────────────────────────────────────────────── 
@asynccontextmanager 
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]: 
    """Manage application startup and shutdown resources."""	
    logger.info("aegis.startup", app_env=settings.app_env)	

    # Initialise Redis connection pool (optional for local dev) 
    try: 
        app.state.redis = aioredis.from_url(	
            settings.redis_url,	
            decode_responses=True, 
            max_connections=20, 
        )	
        await app.state.redis.ping()	
        logger.info("redis.connected", url=settings.redis_url)	
    except Exception as exc: 
        logger.warning("redis.connection_failed_continuing_in_memory", error=str(exc)) 
        app.state.redis = None	

    yield 

    # Graceful shutdown	
    if getattr(app.state, "redis", None):	
        await app.state.redis.close() 
    logger.info("aegis.shutdown") 


# ─── App Factory ─────────────────────────────────────────────────────────────	
def create_app() -> FastAPI: 
    """Build and configure the FastAPI application."""	
    app = FastAPI( 
        title="AEGIS — AI-Generated Code Trust Framework",	
        description=(	
            "Detect AI-generated code, scan for AI-specific security vulnerabilities, " 
            "and verify cryptographic authorship watermarks." 
        ),	
        version="1.0.0", 
        docs_url="/docs", 
        redoc_url="/redoc", 
        lifespan=lifespan,	
    )	

    # CORS 
    app.add_middleware( 
        CORSMiddleware,	
        allow_origins=settings.cors_origin_list, 
        allow_credentials=True,	
        allow_methods=["*"], 
        allow_headers=["*"], 
    )	

    # Mount API	
    app.include_router(api_router, prefix="/api") 

    return app	


app = create_app()	
