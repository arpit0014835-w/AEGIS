""" 
AEGIS — Proof Verify Service 
===============================	
Steganographic authorship watermarking and SHA-256-based verification.	

Provides two capabilities: 
  1. **Embed** — Encode author identity into code via whitespace steganography 
  2. **Verify** — Extract and validate watermarks against claimed authorship	
"""	

from __future__ import annotations 

from pathlib import Path 

from models.report import ProofVerifyResult, WatermarkInfo	
from utils.crypto import (	
    embed_watermark,	
    extract_watermark, 
    generate_author_hash, 
    sha256_file, 
    verify_watermark, 
) 
from utils.logger import get_logger	

logger = get_logger(__name__)	


# ─── Analysis Mode (Scan) ────────────────────────────────────────────────── 

async def run_proof_verify( 
    source_files: list[Path],	
    claimed_author: str | None = None,	
) -> ProofVerifyResult: 
    """ 
    Analyse source files for authorship watermarks.	

    For each file:	
    1. Attempt to extract a watermark from trailing whitespace	
    2. If a claimed_author is provided, verify the watermark against it 
    3. Calculate file hash for integrity checking 

    Parameters	
    ---------- 
    source_files : list[Path]	
        Source files to analyse.	
    claimed_author : str | None 
        Optional author ID to verify watermarks against. 

    Returns	
    ------- 
    ProofVerifyResult	
        Watermark analysis with per-file details. 
    """	
    logger.info(	
        "proof_verify.start", 
        file_count=len(source_files), 
        has_claimed_author=bool(claimed_author),	
    ) 

    watermarks: list[WatermarkInfo] = [] 
    watermarked_count = 0 
    verified_count = 0	

    for file_path in source_files:	
        try: 
            content = file_path.read_text(encoding="utf-8", errors="replace") 
        except Exception as exc:	
            logger.warning("proof_verify.read_failed", path=str(file_path), error=str(exc)) 
            watermarks.append(WatermarkInfo(file_path=str(file_path)))	
            continue 

        # Attempt extraction 
        extracted = extract_watermark(content, bit_count=64)	
        is_watermarked = extracted is not None	

        verified = None 
        confidence = 0.0	
        author_hash = None	

        if is_watermarked: 
            watermarked_count += 1
            confidence = 0.7  # Base confidence when watermark found

            if claimed_author:
                is_verified = verify_watermark(content, claimed_author)
                verified = is_verified
                if is_verified:
                    verified_count += 1
                    confidence = 1.0
                    author_hash = generate_author_hash(claimed_author)[:16]
                else:
                    confidence = 0.3  # Watermark found but doesn't match
        else:
            confidence = 0.0

        watermarks.append(WatermarkInfo(
            file_path=str(file_path),
            is_watermarked=is_watermarked,
            author_hash=author_hash,
            verified=verified,
            confidence=round(confidence, 4),
        ))

    # Score calculation
    total = len(source_files)
    if total > 0 and claimed_author:
        score = (verified_count / total) * 100.0
    elif total > 0:
        score = (watermarked_count / total) * 100.0
    else:
        score = 0.0

    result = ProofVerifyResult(
        watermarks=watermarks,
        total_files=total,
        watermarked_files=watermarked_count,
        verified_files=verified_count,
        score=round(score, 2),
    )

    logger.info(
        "proof_verify.complete",
        score=result.score,
        watermarked=watermarked_count,
        verified=verified_count,
        total=total,
    )
    return result


# ─── Embedding Mode (Authoring Tool) ───────────────────────────────────────

async def watermark_file(
    file_path: Path,
    author_id: str,
    salt: str = "",
) -> str:
    """
    Embed an authorship watermark into a source file.

    Parameters
    ----------
    file_path : Path
        Source file to watermark.
    author_id : str
        Author's unique identifier.
    salt : str
        Optional salt for the hash.

    Returns
    -------
    str
        Watermarked source code.
    """
    content = file_path.read_text(encoding="utf-8")
    author_hash = generate_author_hash(author_id, salt)
    watermarked = embed_watermark(content, author_hash)

    logger.info(
        "proof_verify.watermark_embedded",
        file=str(file_path),
        author_hash=author_hash[:16],
    )
    return watermarked


async def watermark_codebase(
    source_files: list[Path],
    author_id: str,
    salt: str = "",
    output_dir: Path | None = None,
) -> int:
    """
    Embed watermarks into all source files in a codebase.

    If output_dir is provided, writes watermarked files there.
    Otherwise, overwrites the original files.

    Returns
    -------
    int
        Number of files watermarked.
    """
    count = 0
    for file_path in source_files:
        try:
            watermarked = await watermark_file(file_path, author_id, salt)

            if output_dir:
                dest = output_dir / file_path.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(watermarked, encoding="utf-8")
            else:
                file_path.write_text(watermarked, encoding="utf-8")

            count += 1
        except Exception as exc:
            logger.error(
                "proof_verify.watermark_failed",
                file=str(file_path),
                error=str(exc),
            )

    logger.info("proof_verify.codebase_watermarked", files=count)
    return count
