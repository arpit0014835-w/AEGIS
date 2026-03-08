""" 
AEGIS — Structured Logging 
============================	
Consistent JSON logging with structlog for observability.	
""" 

from __future__ import annotations 

import logging	
import sys	

import structlog 
from config import settings 


def _configure_structlog() -> None:	
    """Configure structlog processors for the application."""	
    shared_processors: list = [	
        structlog.contextvars.merge_contextvars, 
        structlog.stdlib.add_log_level, 
        structlog.stdlib.add_logger_name, 
        structlog.processors.TimeStamper(fmt="iso"), 
        structlog.processors.StackInfoRenderer(), 
        structlog.processors.UnicodeDecoder(),	
    ]	

    if settings.app_env == "development": 
        renderer = structlog.dev.ConsoleRenderer(colors=True) 
    else:	
        renderer = structlog.processors.JSONRenderer()	

    structlog.configure( 
        processors=[ 
            *shared_processors,	
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,	
        ],	
        logger_factory=structlog.stdlib.LoggerFactory(), 
        wrapper_class=structlog.stdlib.BoundLogger, 
        cache_logger_on_first_use=True,	
    ) 

    formatter = structlog.stdlib.ProcessorFormatter(	
        processors=[	
            structlog.stdlib.ProcessorFormatter.remove_processors_meta, 
            renderer, 
        ],	
    ) 

    handler = logging.StreamHandler(sys.stdout)	
    handler.setFormatter(formatter) 

    root = logging.getLogger()	
    root.handlers.clear()	
    root.addHandler(handler) 
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO)) 


# Run configuration on import	
_configure_structlog() 


def get_logger(name: str) -> structlog.stdlib.BoundLogger: 
    """Return a named, bound logger instance.""" 
    return structlog.get_logger(name)	
