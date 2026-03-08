""" 
AEGIS — Report Retrieval Endpoints 
=====================================	
Fetch the full Trust Score report for a completed scan.	

Note: Modifed to use in-memory store for native Windows execution. 
""" 

from __future__ import annotations	

from uuid import UUID	

from fastapi import APIRouter, HTTPException, status 

from models.report import TrustScoreReport 
from utils.logger import get_logger	

# Import the in-memory store from scans.py	
from api.v1.scans import _REPORTS_STORE	

router = APIRouter() 
logger = get_logger(__name__) 


@router.get( 
    "/reports/{scan_id}", 
    response_model=TrustScoreReport, 
    summary="Get full analysis report",	
)	
async def get_report(scan_id: UUID) -> TrustScoreReport: 
    """ 
    Retrieve the complete Trust Score report for a finished scan.	

    Returns the composite score with full breakdowns for	
    Ghost Detect, Breach Secure, and Proof Verify modules. 
    """ 
    report = _REPORTS_STORE.get(str(scan_id))	
    if not report:	
        raise HTTPException(	
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=( 
                f"Report for scan '{scan_id}' not found. "	
                "The scan may still be in progress or the ID is invalid." 
            ),	
        )	

    logger.info("report.retrieved", scan_id=str(scan_id)) 
    return report 
