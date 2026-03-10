""" 
AEGIS Backend — Application Configuration 
==========================================	
Centralised settings loaded from environment variables via Pydantic BaseSettings.	
""" 

from __future__ import annotations 

from pathlib import Path	
from typing import Optional	

from pydantic import Field 
from pydantic_settings import BaseSettings, SettingsConfigDict 


class Settings(BaseSettings):	
    """Root application settings — all values can be overridden via env vars."""	

    model_config = SettingsConfigDict(	
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=False, 
        extra="ignore", 
    ) 

    # ─── Application ────────────────────────────────────────────	
    app_name: str = "aegis"	
    app_env: str = "development" 
    debug: bool = True 
    log_level: str = "INFO"	

    # ─── Server ─────────────────────────────────────────────────	
    backend_host: str = "0.0.0.0" 
    backend_port: int = 8000 
    cors_origins: str = "*"	

    # ─── Redis ──────────────────────────────────────────────────	
    redis_url: str = "redis://localhost:6379/0"	
    redis_queue_name: str = "aegis:scan_jobs" 
    redis_result_ttl: int = Field(default=3600, description="Report TTL in seconds") 

    # ─── Azure OpenAI (optional) ────────────────────────────────	
    azure_openai_endpoint: Optional[str] = None 
    azure_openai_api_key: Optional[str] = None	
    azure_openai_deployment: str = "gpt-4o"	
    azure_openai_api_version: str = "2024-02-15-preview" 

    # ─── Azure AI Content Safety (optional) ───────────────────── 
    azure_content_safety_endpoint: Optional[str] = None	
    azure_content_safety_api_key: Optional[str] = None 

    # ─── Scanning ───────────────────────────────────────────────	
    semgrep_rules_dir: str = "rules/semgrep" 
    upload_dir: str = "./tmp/uploads"	
    clone_dir: str = "./tmp/repos"	
    max_repo_size_mb: int = 500 
    scan_timeout_seconds: int = 600 

    # ─── Derived Helpers ────────────────────────────────────────	
    @property 
    def cors_origin_list(self) -> list[str]: 
        return [o.strip() for o in self.cors_origins.split(",")] 

    @property	
    def upload_path(self) -> Path:	
        p = Path(self.upload_dir) 
        p.mkdir(parents=True, exist_ok=True) 
        return p	

    @property 
    def clone_path(self) -> Path:	
        p = Path(self.clone_dir) 
        p.mkdir(parents=True, exist_ok=True) 
        return p	

    @property	
    def is_azure_openai_configured(self) -> bool: 
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)	

    @property	
    def is_content_safety_configured(self) -> bool: 
        return bool(self.azure_content_safety_endpoint and self.azure_content_safety_api_key)


# Singleton — import this everywhere
settings = Settings()
