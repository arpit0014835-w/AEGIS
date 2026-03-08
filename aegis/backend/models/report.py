""" 
AEGIS — Report & Trust Score Models 
=====================================	
Pydantic models for analysis results and the composite Trust Score report.	
""" 

from __future__ import annotations 

from datetime import datetime, timezone	
from typing import Optional	
from uuid import UUID 

from pydantic import BaseModel, Field 

from models.enums import Language, Severity, VulnerabilityCategory	


# ─── File-Level Analysis ────────────────────────────────────────────────────	

class FileAnalysis(BaseModel):	
    """Per-file analysis metadata.""" 
    file_path: str 
    language: Language = Language.UNKNOWN 
    line_count: int = 0 
    function_count: int = 0 
    ai_probability: float = Field(	
        default=0.0,	
        ge=0.0, 
        le=1.0, 
        description="Probability that the file is AI-generated (0.0–1.0).",	
    )	
    style_consistency_score: float = Field( 
        default=1.0, 
        ge=0.0,	
        le=1.0,	
        description="How consistent the style is with the rest of the codebase.",	
    )
    detection_method: str = Field(
        default="unknown",
        description="Method used for AI detection: 'ml_model', 'heuristic', or 'skipped'.",
    )


# ─── Ghost Detect ──────────────────────────────────────────────────────────── 

class HallucinatedDependency(BaseModel):	
    """A dependency that does not exist in public registries.""" 
    package_name: str	
    file_path: str	
    line_number: int 
    registry: str = Field(description="'pypi' or 'npm'") 


class GhostDetectResult(BaseModel):	
    """Output of the Ghost Detect analysis module.""" 
    overall_ai_probability: float = Field(default=0.0, ge=0.0, le=1.0)	
    file_analyses: list[FileAnalysis] = Field(default_factory=list) 
    hallucinated_dependencies: list[HallucinatedDependency] = Field(default_factory=list)	
    style_anomaly_count: int = 0	
    score: float = Field( 
        default=100.0, 
        ge=0.0,	
        le=100.0, 
        description="Ghost Detect sub-score (100 = fully human, 0 = fully AI).", 
    ) 


# ─── Breach Secure ──────────────────────────────────────────────────────────	

class Vulnerability(BaseModel):	
    """A single detected vulnerability.""" 
    rule_id: str 
    category: VulnerabilityCategory	
    severity: Severity 
    file_path: str	
    line_start: int 
    line_end: int 
    message: str	
    snippet: Optional[str] = None	
    fix_suggestion: Optional[str] = None 


class BreachSecureResult(BaseModel):	
    """Output of the Breach Secure analysis module."""	
    vulnerabilities: list[Vulnerability] = Field(default_factory=list) 
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    score: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Breach Secure sub-score (100 = clean, 0 = severely compromised).",
    )


# ─── Proof Verify ───────────────────────────────────────────────────────────

class WatermarkInfo(BaseModel):
    """Watermark verification details for a file."""
    file_path: str
    is_watermarked: bool = False
    author_hash: Optional[str] = None
    verified: Optional[bool] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ProofVerifyResult(BaseModel):
    """Output of the Proof Verify analysis module."""
    watermarks: list[WatermarkInfo] = Field(default_factory=list)
    total_files: int = 0
    watermarked_files: int = 0
    verified_files: int = 0
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Proof Verify sub-score (100 = fully verified, 0 = no watermarks).",
    )


# ─── Trust Score Report ─────────────────────────────────────────────────────

class TrustScoreBreakdown(BaseModel):
    """Weighted breakdown of the composite Trust Score."""
    ghost_detect_score: float = 0.0
    ghost_detect_weight: float = 0.35
    breach_secure_score: float = 0.0
    breach_secure_weight: float = 0.40
    proof_verify_score: float = 0.0
    proof_verify_weight: float = 0.25


class TrustScoreReport(BaseModel):
    """Complete analysis report with composite Trust Score."""
    scan_id: UUID
    trust_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Composite Trust Score (0–100).",
    )
    breakdown: TrustScoreBreakdown = Field(default_factory=TrustScoreBreakdown)
    ghost_detect: GhostDetectResult = Field(default_factory=GhostDetectResult)
    breach_secure: BreachSecureResult = Field(default_factory=BreachSecureResult)
    proof_verify: ProofVerifyResult = Field(default_factory=ProofVerifyResult)
    total_files_analyzed: int = 0
    languages_detected: list[Language] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
