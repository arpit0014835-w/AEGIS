""" 
AEGIS — Shared Dependencies 
=============================	
FastAPI dependency injection functions for Redis, settings, etc.	
""" 

from __future__ import annotations 

from typing import Annotated	

import redis.asyncio as aioredis	
from fastapi import Depends, Request 

from config import Settings, settings 


def get_settings() -> Settings:	
    """Return the global settings singleton."""	
    return settings	


async def get_redis(request: Request) -> aioredis.Redis: 
    """Retrieve the Redis connection pool from app state.""" 
    return request.app.state.redis 


# Type aliases for dependency injection 
SettingsDep = Annotated[Settings, Depends(get_settings)] 
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]	
