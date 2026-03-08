""" 
AEGIS — Trust Score Tests 
===========================	
"""	

from __future__ import annotations 

from uuid import uuid4 

import pytest	

from models.report import (	
    BreachSecureResult, 
    GhostDetectResult, 
    ProofVerifyResult,	
)	
from services.trust_score import (	
    BREACH_SECURE_WEIGHT, 
    GHOST_DETECT_WEIGHT, 
    PROOF_VERIFY_WEIGHT, 
    compute_trust_score, 
) 


class TestWeightConfiguration:	
    """Verify weight configuration is correct."""	

    def test_weights_sum_to_one(self): 
        total = GHOST_DETECT_WEIGHT + BREACH_SECURE_WEIGHT + PROOF_VERIFY_WEIGHT 
        assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"	

    def test_weights_are_positive(self):	
        assert GHOST_DETECT_WEIGHT > 0 
        assert BREACH_SECURE_WEIGHT > 0 
        assert PROOF_VERIFY_WEIGHT > 0	


class TestTrustScoreComputation:	
    """Test the Trust Score computation logic."""	

    def test_perfect_scores(self): 
        """All modules report 100 → Trust Score should be 100.""" 
        report = compute_trust_score(	
            scan_id=uuid4(), 
            ghost_detect=GhostDetectResult(score=100.0),	
            breach_secure=BreachSecureResult(score=100.0),	
            proof_verify=ProofVerifyResult(score=100.0), 
        ) 
        assert report.trust_score == 100.0	

    def test_zero_scores(self): 
        """All modules report 0 → Trust Score should be 0."""	
        report = compute_trust_score( 
            scan_id=uuid4(),	
            ghost_detect=GhostDetectResult(score=0.0),	
            breach_secure=BreachSecureResult(score=0.0), 
            proof_verify=ProofVerifyResult(score=0.0), 
        )	
        assert report.trust_score == 0.0 

    def test_weighted_calculation(self): 
        """Verify the weighted average is correct.""" 
        ghost_score = 80.0	
        breach_score = 60.0	
        proof_score = 90.0 

        expected = ( 
            ghost_score * GHOST_DETECT_WEIGHT	
            + breach_score * BREACH_SECURE_WEIGHT 
            + proof_score * PROOF_VERIFY_WEIGHT	
        ) 

        report = compute_trust_score( 
            scan_id=uuid4(),	
            ghost_detect=GhostDetectResult(score=ghost_score),	
            breach_secure=BreachSecureResult(score=breach_score), 
            proof_verify=ProofVerifyResult(score=proof_score),	
        )	

        assert abs(report.trust_score - round(expected, 2)) < 0.01 

    def test_breach_secure_highest_weight(self):
        """Breach Secure has 40% weight, so it should have the most impact."""
        # Only breach_secure is 0 → trust score should be lower than if only ghost is 0
        breach_low = compute_trust_score(
            scan_id=uuid4(),
            ghost_detect=GhostDetectResult(score=100.0),
            breach_secure=BreachSecureResult(score=0.0),
            proof_verify=ProofVerifyResult(score=100.0),
        )
        ghost_low = compute_trust_score(
            scan_id=uuid4(),
            ghost_detect=GhostDetectResult(score=0.0),
            breach_secure=BreachSecureResult(score=100.0),
            proof_verify=ProofVerifyResult(score=100.0),
        )
        assert breach_low.trust_score < ghost_low.trust_score

    def test_report_contains_breakdown(self):
        """Verify the breakdown is properly populated."""
        report = compute_trust_score(
            scan_id=uuid4(),
            ghost_detect=GhostDetectResult(score=75.0),
            breach_secure=BreachSecureResult(score=50.0),
            proof_verify=ProofVerifyResult(score=90.0),
            total_files=10,
        )
        assert report.breakdown.ghost_detect_score == 75.0
        assert report.breakdown.breach_secure_score == 50.0
        assert report.breakdown.proof_verify_score == 90.0
        assert report.total_files_analyzed == 10

    def test_score_clamped_to_range(self):
        """Score should never exceed 100 or go below 0."""
        report = compute_trust_score(
            scan_id=uuid4(),
            ghost_detect=GhostDetectResult(score=100.0),
            breach_secure=BreachSecureResult(score=100.0),
            proof_verify=ProofVerifyResult(score=100.0),
        )
        assert 0 <= report.trust_score <= 100

    def test_scan_id_preserved(self):
        """Scan ID should be passed through to the report."""
        sid = uuid4()
        report = compute_trust_score(
            scan_id=sid,
            ghost_detect=GhostDetectResult(score=50.0),
            breach_secure=BreachSecureResult(score=50.0),
            proof_verify=ProofVerifyResult(score=50.0),
        )
        assert report.scan_id == sid
