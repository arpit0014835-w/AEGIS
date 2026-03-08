""" 
AEGIS — Scan Job Models 
========================	
Pydantic models for scan requests, jobs, and status tracking.	
""" 

from __future__ import annotations 

from datetime import datetime, timezone	
from typing import Optional	
from uuid import UUID, uuid4 

from pydantic import BaseModel, Field, HttpUrl 

from models.enums import InputType, ScanStatus	


# ─── Request / Response ─────────────────────────────────────────────────────	

class ScanRequest(BaseModel):	
    """Payload accepted by POST /api/v1/scans.""" 
    repo_url: Optional[HttpUrl] = Field( 
        default=None, 
        description="GitHub repository URL to scan.", 
        examples=["https://github.com/owner/repo"], 
    )	

    class Config:	
        json_schema_extra = { 
            "example": { 
                "repo_url": "https://github.com/owner/repo",	
            }	
        } 


class ScanStatusResponse(BaseModel): 
    """Response returned by GET /api/v1/scans/{scan_id}."""	
    scan_id: UUID	
    status: ScanStatus	
    input_type: InputType 
    repo_url: Optional[str] = None 
    progress: float = Field(	
        default=0.0, 
        ge=0.0,	
        le=100.0,	
        description="Scan progress percentage.", 
    ) 
    current_stage: Optional[str] = None	
    created_at: datetime 
    updated_at: datetime	
    error: Optional[str] = None 


# ─── Internal Job ────────────────────────────────────────────────────────────	

class ScanJob(BaseModel):	
    """Internal representation of a scan job stored in Redis.""" 
    scan_id: UUID = Field(default_factory=uuid4) 
    status: ScanStatus = ScanStatus.QUEUED	
    input_type: InputType = InputType.GITHUB_URL 
    repo_url: Optional[str] = None 
    upload_path: Optional[str] = None 
    clone_path: Optional[str] = None	
    progress: float = 0.0	
    current_stage: Optional[str] = None 
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) 
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))	
    error: Optional[str] = None 

    def advance(self, status: ScanStatus, progress: float) -> None:	
        """Transition to the next pipeline stage.""" 
        self.status = status 
        self.current_stage = status.value	
        self.progress = progress	
        self.updated_at = datetime.now(timezone.utc) 

    def fail(self, error: str) -> None:	
        """Mark the job as failed."""	
        self.status = ScanStatus.FAILED 
        self.error = error
        self.updated_at = datetime.now(timezone.utc)
