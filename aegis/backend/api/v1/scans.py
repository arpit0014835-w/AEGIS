""" 
AEGIS — Scan Submission & Status Endpoints 
============================================	
Create new scan jobs and poll their progress.	

Note: Modifed to use in-memory jobs and BackgroundTasks for native Windows execution 
without requiring an external Redis server. 
"""	

from __future__ import annotations	

import json 
import shutil 
import asyncio
import threading
from pathlib import Path
from uuid import UUID, uuid4
from typing import Dict, Any 

from fastapi import APIRouter, HTTPException, UploadFile, File, status, BackgroundTasks 

from api.deps import SettingsDep 
from models.enums import InputType, ScanStatus 
from models.scan import ScanJob, ScanRequest, ScanStatusResponse 
from utils.logger import get_logger	

# Import analysis services directly for background processing	
from services.ingestion import ingest_repository 
from services.ghost_detect import run_ghost_detect 
from services.breach_secure import run_breach_secure	
from services.proof_verify import run_proof_verify	
from services.trust_score import compute_trust_score 
from utils.git_ops import cleanup_clone 

router = APIRouter()	
logger = get_logger(__name__)	

# ─── In-Memory Store ─────────────────────────────────────────────────────────	
# Replacing Redis temporarily for native Windows execution 
_JOBS_STORE: Dict[str, ScanJob] = {} 
_REPORTS_STORE: Dict[str, Any] = {}	

def get_job(scan_id: str | UUID) -> ScanJob | None: 
    return _JOBS_STORE.get(str(scan_id))	

def save_job(job: ScanJob) -> None:	
    _JOBS_STORE[str(job.scan_id)] = job 


# ─── Background Execution ──────────────────────────────────────────────────── 

def _start_scan_thread(job: ScanJob) -> None:
    """Launch the scan in a separate thread with its own event loop."""
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_execute_scan_background(job))
        finally:
            loop.close()
    t = threading.Thread(target=_run, daemon=True)
    t.start()

async def _execute_scan_background(job: ScanJob) -> None:	
    """Execute the full analysis pipeline for a scan job in the background.""" 
    try:	
        # Stage 1: Ingestion 
        job.advance(ScanStatus.CLONING, 10.0)	
        save_job(job)	

        ingestion = await ingest_repository( 
            scan_id=job.scan_id, 
            input_type=job.input_type,	
            repo_url=job.repo_url, 
            upload_path=job.upload_path, 
        ) 

        job.advance(ScanStatus.PARSING, 20.0)	
        save_job(job)	

        logger.info( 
            "worker.ingestion_done", 
            scan_id=str(job.scan_id),	
            files=ingestion.total_files, 
            lines=ingestion.total_lines,	
        ) 

        # Stage 2: Ghost Detect 
        job.advance(ScanStatus.GHOST_DETECT, 40.0)	
        save_job(job)	

        ghost_result = await run_ghost_detect( 
            parsed_files=ingestion.parsed_files,	
            source_files=ingestion.source_files,	
        ) 

        # Stage 3: Breach Secure
        job.advance(ScanStatus.BREACH_SECURE, 65.0)
        save_job(job)

        breach_result = await run_breach_secure(
            source_files=ingestion.source_files,
            target_dir=str(ingestion.root_path),
        )

        # Stage 4: Proof Verify
        job.advance(ScanStatus.PROOF_VERIFY, 85.0)
        save_job(job)

        proof_result = await run_proof_verify(
            source_files=ingestion.source_files,
        )

        # Stage 5: Score Aggregation
        job.advance(ScanStatus.SCORING, 95.0)
        save_job(job)

        languages = list({pf.language for pf in ingestion.parsed_files})

        report = compute_trust_score(
            scan_id=job.scan_id,
            ghost_detect=ghost_result,
            breach_secure=breach_result,
            proof_verify=proof_result,
            total_files=ingestion.total_files,
            languages=languages,
        )

        # Store report
        _REPORTS_STORE[str(job.scan_id)] = report

        # Done
        job.advance(ScanStatus.COMPLETED, 100.0)
        save_job(job)

        logger.info(
            "worker.scan_complete",
            scan_id=str(job.scan_id),
            trust_score=report.trust_score,
        )

    except Exception as exc:
        logger.error(
            "worker.scan_failed",
            scan_id=str(job.scan_id),
            error=str(exc),
            exc_info=True,
        )
        job.fail(str(exc))
        save_job(job)

    finally:
        # Cleanup cloned/extracted files
        try:
            cleanup_clone(job.scan_id)
        except Exception:
            pass

# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post(
    "/scans",
    response_model=ScanStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a new scan",
)
async def create_scan(
    request: ScanRequest,
    settings: SettingsDep,
    background_tasks: BackgroundTasks,
) -> ScanStatusResponse:
    """Submit a GitHub repository URL for analysis."""
    if not request.repo_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'repo_url' must be provided.",
        )

    job = ScanJob(
        scan_id=uuid4(),
        input_type=InputType.GITHUB_URL,
        repo_url=str(request.repo_url),
    )

    # Save to memory and start scan in a separate thread
    save_job(job)
    _start_scan_thread(job)

    logger.info("scan.started_background", scan_id=str(job.scan_id))

    return ScanStatusResponse(
        scan_id=job.scan_id,
        status=job.status,
        input_type=job.input_type,
        repo_url=job.repo_url,
        progress=job.progress,
        current_stage=job.current_stage,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


# Accepted archive extensions
_ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".tar.gz", ".tar.bz2", ".bz2", ".xz", ".tar.xz"}
# Accepted source file extensions for direct upload
_SOURCE_EXTENSIONS = {
    ".py", ".pyw", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".java", ".kt", ".kts", ".scala", ".groovy",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rs", ".go",
    ".swift", ".dart", ".m", ".mm",
    ".rb", ".php", ".lua", ".pl", ".r", ".R",
    ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
    ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".vue", ".svelte",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".ini", ".cfg",
    ".sql", ".md", ".rst", ".tf", ".hcl", ".dockerfile",
}
_ALL_ACCEPTED = _ARCHIVE_EXTENSIONS | _SOURCE_EXTENSIONS


def _get_file_ext(filename: str) -> str:
    """Get the file extension, handling double extensions like .tar.gz."""
    lower = filename.lower()
    for double in (".tar.gz", ".tar.bz2", ".tar.xz"):
        if lower.endswith(double):
            return double
    return Path(filename).suffix.lower()


@router.post(
    "/scans/upload",
    response_model=ScanStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a file for scanning",
)
async def upload_scan(
    settings: SettingsDep,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Archive or source file to analyse"),
) -> ScanStatusResponse:
    """Upload an archive or source file for analysis."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    ext = _get_file_ext(file.filename)
    if ext not in _ALL_ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Accepted: archives (.zip, .rar, .7z, .tar.gz, etc.) and source files (.py, .js, .java, etc.).",
        )

    is_archive = ext in _ARCHIVE_EXTENSIONS
    scan_id = uuid4()
    dest = settings.upload_path / f"{scan_id}{ext}"

    # Stream upload to disk
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    job = ScanJob(
        scan_id=scan_id,
        input_type=InputType.ZIP_UPLOAD if is_archive else InputType.FILE_UPLOAD,
        upload_path=str(dest),
    )

    # Save to memory and start scan in a separate thread
    save_job(job)
    _start_scan_thread(job)

    logger.info("scan.started_background_zip", scan_id=str(job.scan_id))

    return ScanStatusResponse(
        scan_id=job.scan_id,
        status=job.status,
        input_type=job.input_type,
        progress=job.progress,
        current_stage=job.current_stage,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get(
    "/scans/{scan_id}",
    response_model=ScanStatusResponse,
    summary="Get scan status",
)
async def get_scan_status(scan_id: UUID) -> ScanStatusResponse:
    """Poll the current status and progress of a scan job."""
    job = get_job(scan_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan '{scan_id}' not found.",
        )

    return ScanStatusResponse(
        scan_id=job.scan_id,
        status=job.status,
        input_type=job.input_type,
        repo_url=job.repo_url,
        progress=job.progress,
        current_stage=job.current_stage,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error=job.error,
    )
