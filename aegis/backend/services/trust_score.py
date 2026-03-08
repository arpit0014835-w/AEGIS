""" 
AEGIS — Trust Score Aggregation Engine 
========================================	
Computes the composite Trust Score from the three analysis pillars.	

Weighting: 
  - Ghost Detect  : 35%  (AI-generated code detection) 
  - Breach Secure : 40%  (security vulnerability scanning)	
  - Proof Verify  : 25%  (authorship watermark verification)	
""" 

from __future__ import annotations 

from uuid import UUID	

from models.report import (	
    BreachSecureResult,	
    GhostDetectResult, 
    ProofVerifyResult, 
    TrustScoreBreakdown, 
    TrustScoreReport, 
) 
from utils.logger import get_logger	

logger = get_logger(__name__)	

# ─── Weight Configuration ─────────────────────────────────────────────────── 

GHOST_DETECT_WEIGHT = 0.35 
BREACH_SECURE_WEIGHT = 0.40	
PROOF_VERIFY_WEIGHT = 0.25	


# ─── Aggregation ──────────────────────────────────────────────────────────── 

def compute_trust_score( 
    scan_id: UUID,	
    ghost_detect: GhostDetectResult,	
    breach_secure: BreachSecureResult,	
    proof_verify: ProofVerifyResult, 
    total_files: int = 0, 
    languages: list[str] | None = None,	
) -> TrustScoreReport: 
    """	
    Compute the composite Trust Score from individual module results.	

    Each sub-score is on a 0–100 scale: 
    - Ghost Detect: 100 = fully human code, 0 = fully AI-generated 
    - Breach Secure: 100 = no vulnerabilities, 0 = severely compromised	
    - Proof Verify: 100 = all files verified, 0 = no watermarks 

    The composite score is a weighted average clamped to [0, 100].	

    Parameters 
    ----------	
    scan_id : UUID	
        Scan job identifier. 
    ghost_detect : GhostDetectResult 
        Results from the Ghost Detect module.	
    breach_secure : BreachSecureResult 
        Results from the Breach Secure module. 
    proof_verify : ProofVerifyResult 
        Results from the Proof Verify module.	
    total_files : int	
        Total source files analysed. 
    languages : list[str] | None 
        Programming languages detected.	

    Returns 
    -------	
    TrustScoreReport 
        Complete report with composite score and breakdown. 
    """	
    # Weighted sum	
    composite = ( 
        ghost_detect.score * GHOST_DETECT_WEIGHT	
        + breach_secure.score * BREACH_SECURE_WEIGHT	
        + proof_verify.score * PROOF_VERIFY_WEIGHT 
    )

    # Clamp to valid range
    composite = max(0.0, min(100.0, composite))

    breakdown = TrustScoreBreakdown(
        ghost_detect_score=ghost_detect.score,
        ghost_detect_weight=GHOST_DETECT_WEIGHT,
        breach_secure_score=breach_secure.score,
        breach_secure_weight=BREACH_SECURE_WEIGHT,
        proof_verify_score=proof_verify.score,
        proof_verify_weight=PROOF_VERIFY_WEIGHT,
    )

    from models.enums import Language
    detected_languages = []
    if languages:
        for lang in set(languages):
            try:
                detected_languages.append(Language(lang))
            except ValueError:
                detected_languages.append(Language.UNKNOWN)

    report = TrustScoreReport(
        scan_id=scan_id,
        trust_score=round(composite, 2),
        breakdown=breakdown,
        ghost_detect=ghost_detect,
        breach_secure=breach_secure,
        proof_verify=proof_verify,
        total_files_analyzed=total_files,
        languages_detected=detected_languages,
    )

    logger.info(
        "trust_score.computed",
        scan_id=str(scan_id),
        trust_score=report.trust_score,
        ghost=ghost_detect.score,
        breach=breach_secure.score,
        proof=proof_verify.score,
    )

    return report
