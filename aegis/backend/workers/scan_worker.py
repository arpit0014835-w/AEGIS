""" 
AEGIS — Scan Worker 
=====================	
Redis queue consumer that orchestrates the full analysis pipeline:	
  Ingestion → Ghost Detect → Breach Secure → Proof Verify → Trust Score 

Runs as a standalone process: ``python -m workers.scan_worker`` 
"""	

from __future__ import annotations	

import asyncio 
import signal 
import sys	
from pathlib import Path	

import redis.asyncio as aioredis	

from config import settings 
from models.enums import InputType, ScanStatus 
from models.scan import ScanJob 
from services.breach_secure import run_breach_secure 
from services.ghost_detect import run_ghost_detect 
from services.ingestion import ingest_repository	
from services.proof_verify import run_proof_verify	
from services.trust_score import compute_trust_score 
from utils.git_ops import cleanup_clone 
from utils.logger import get_logger	

logger = get_logger(__name__)	

# Graceful shutdown 
_shutdown = asyncio.Event() 


def _signal_handler(sig, frame):	
    logger.info("worker.shutdown_signal", signal=sig)	
    _shutdown.set()	


# ─── Job Execution ────────────────────────────────────────────────────────── 

async def _update_job(redis: aioredis.Redis, job: ScanJob) -> None: 
    """Persist the latest job state to Redis."""	
    key = f"aegis:scan:{job.scan_id}" 
    await redis.set(key, job.model_dump_json())	


async def _execute_scan(redis: aioredis.Redis, job: ScanJob) -> None:	
    """ 
    Execute the full analysis pipeline for a scan job. 

    Pipeline stages (with progress %):	
      10% — Cloning / Extracting 
      20% — Parsing	
      40% — Ghost Detect 
      65% — Breach Secure	
      85% — Proof Verify	
      95% — Scoring 
     100% — Completed 
    """	
    try: 
        # ─── Stage 1: Ingestion ───────────────────────────────────── 
        job.advance(ScanStatus.CLONING, 10.0) 
        await _update_job(redis, job)	

        ingestion = await ingest_repository(	
            scan_id=job.scan_id, 
            input_type=job.input_type, 
            repo_url=job.repo_url,	
            upload_path=job.upload_path, 
        )	

        job.advance(ScanStatus.PARSING, 20.0) 
        await _update_job(redis, job) 

        logger.info(	
            "worker.ingestion_done",	
            scan_id=str(job.scan_id), 
            files=ingestion.total_files,	
            lines=ingestion.total_lines,	
        ) 

        # ─── Stage 2: Ghost Detect ─────────────────────────────────
        job.advance(ScanStatus.GHOST_DETECT, 40.0)
        await _update_job(redis, job)

        ghost_result = await run_ghost_detect(
            parsed_files=ingestion.parsed_files,
            source_files=ingestion.source_files,
        )

        # ─── Stage 3: Breach Secure ────────────────────────────────
        job.advance(ScanStatus.BREACH_SECURE, 65.0)
        await _update_job(redis, job)

        breach_result = await run_breach_secure(
            source_files=ingestion.source_files,
            target_dir=str(ingestion.root_path),
        )

        # ─── Stage 4: Proof Verify ─────────────────────────────────
        job.advance(ScanStatus.PROOF_VERIFY, 85.0)
        await _update_job(redis, job)

        proof_result = await run_proof_verify(
            source_files=ingestion.source_files,
        )

        # ─── Stage 5: Score Aggregation ─────────────────────────────
        job.advance(ScanStatus.SCORING, 95.0)
        await _update_job(redis, job)

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
        report_key = f"aegis:report:{job.scan_id}"
        await redis.set(
            report_key,
            report.model_dump_json(),
            ex=settings.redis_result_ttl,
        )

        # ─── Done ──────────────────────────────────────────────────
        job.advance(ScanStatus.COMPLETED, 100.0)
        await _update_job(redis, job)

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
        await _update_job(redis, job)

    finally:
        # Cleanup cloned/extracted files
        try:
            cleanup_clone(job.scan_id)
        except Exception:
            pass


# ─── Main Loop ──────────────────────────────────────────────────────────────

async def run_worker() -> None:
    """
    Main worker loop — consumes scan jobs from the Redis queue.

    Uses BRPOP for blocking reads with a 5-second timeout.
    """
    logger.info("worker.starting", queue=settings.redis_queue_name)

    redis = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=10,
    )

    try:
        await redis.ping()
        logger.info("worker.redis_connected")
    except Exception as exc:
        logger.error("worker.redis_failed", error=str(exc))
        return

    while not _shutdown.is_set():
        try:
            # Blocking pop with timeout
            result = await redis.brpop(settings.redis_queue_name, timeout=5)
            if result is None:
                continue

            _, scan_id = result
            logger.info("worker.job_received", scan_id=scan_id)

            # Load job data
            key = f"aegis:scan:{scan_id}"
            raw = await redis.get(key)
            if not raw:
                logger.warning("worker.job_not_found", scan_id=scan_id)
                continue

            job = ScanJob.model_validate_json(raw)
            await _execute_scan(redis, job)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("worker.loop_error", error=str(exc))
            await asyncio.sleep(1)

    await redis.close()
    logger.info("worker.stopped")


# ─── Entrypoint ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("worker.interrupted")
        sys.exit(0)
