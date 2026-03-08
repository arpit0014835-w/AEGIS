""" 
AEGIS — Ingestion Service 
===========================	
Repository cloning, ZIP extraction, and codebase parsing orchestration.	
""" 

from __future__ import annotations 

import shutil	
import zipfile	
from pathlib import Path 
from uuid import UUID 

from models.enums import InputType	
from utils.file_parser import ParsedFile, parse_codebase	
from utils.git_ops import clone_repository, enumerate_source_files, SUPPORTED_EXTENSIONS	
from utils.logger import get_logger 

logger = get_logger(__name__) 


class IngestionResult: 
    """Result of the ingestion phase.""" 

    def __init__( 
        self,	
        root_path: Path,	
        source_files: list[Path], 
        parsed_files: list[ParsedFile], 
    ):	
        self.root_path = root_path	
        self.source_files = source_files 
        self.parsed_files = parsed_files 
        self.total_files = len(source_files)	
        self.total_lines = sum(pf.line_count for pf in parsed_files)	


async def ingest_repository(	
    scan_id: UUID, 
    input_type: InputType, 
    repo_url: str | None = None,	
    upload_path: str | None = None, 
) -> IngestionResult:	
    """	
    Ingest a codebase from a Git URL or ZIP archive. 

    Pipeline: 
    1. Clone repository or extract ZIP	
    2. Enumerate source files (filter by extension, skip vendors) 
    3. Parse each file for AST-level metadata	

    Returns 
    -------	
    IngestionResult	
        Structured data for downstream analysis modules. 
    """ 
    root_path: Path	

    if input_type == InputType.GITHUB_URL: 
        if not repo_url: 
            raise ValueError("repo_url is required for GITHUB_URL input type") 
        root_path = clone_repository(repo_url, scan_id)	
    elif input_type == InputType.ZIP_UPLOAD:	
        if not upload_path: 
            raise ValueError("upload_path is required for ZIP_UPLOAD input type") 
        root_path = _extract_archive(upload_path, scan_id)	
    elif input_type == InputType.FILE_UPLOAD: 
        if not upload_path:	
            raise ValueError("upload_path is required for FILE_UPLOAD input type") 
        root_path = _stage_single_file(upload_path, scan_id) 
    else:	
        raise ValueError("Unsupported input type: " + str(input_type))	

    # Enumerate and parse 
    source_files = enumerate_source_files(root_path)	
    parsed_files = parse_codebase(source_files)	

    logger.info( 
        "ingestion.complete",
        scan_id=str(scan_id),
        files=len(source_files),
        lines=sum(pf.line_count for pf in parsed_files),
    )

    return IngestionResult(
        root_path=root_path,
        source_files=source_files,
        parsed_files=parsed_files,
    )


def _extract_archive(archive_path: str, scan_id: UUID) -> Path:
    """Extract an archive (.zip, .rar, .7z, .tar.*, etc.) to a temp directory."""
    from config import settings
    import tarfile

    dest = settings.clone_path / str(scan_id)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    lower = archive_path.lower()
    logger.info("archive.extract.start", path=archive_path, dest=str(dest))

    if lower.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            for member in zf.namelist():
                member_path = Path(member)
                if member_path.is_absolute() or ".." in member_path.parts:
                    logger.warning("zip.path_traversal_blocked", member=member)
                    continue
                zf.extract(member, dest)
    elif lower.endswith((".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".tar")):
        mode = "r:gz" if lower.endswith((".tar.gz", ".tgz")) else \
               "r:bz2" if lower.endswith(".tar.bz2") else \
               "r:xz" if lower.endswith(".tar.xz") else "r:"
        with tarfile.open(archive_path, mode) as tf:
            for member in tf.getmembers():
                member_path = Path(member.name)
                if member_path.is_absolute() or ".." in member_path.parts:
                    logger.warning("tar.path_traversal_blocked", member=member.name)
                    continue
                tf.extract(member, dest, filter="data")
    elif lower.endswith(".rar"):
        # Try rarfile (Python library) first, then 7z CLI
        try:
            import rarfile
            with rarfile.RarFile(archive_path) as rf:
                for member in rf.namelist():
                    member_path = Path(member)
                    if member_path.is_absolute() or ".." in member_path.parts:
                        logger.warning("rar.path_traversal_blocked", member=member)
                        continue
                    rf.extract(member, dest)
        except ImportError:
            import subprocess
            try:
                result = subprocess.run(
                    ["7z", "x", archive_path, f"-o{dest}", "-y"],
                    capture_output=True, text=True,
                )
                if result.returncode != 0:
                    raise RuntimeError(result.stderr)
            except FileNotFoundError:
                raise RuntimeError(
                    "Cannot extract .rar files: install 'unrar' (e.g. winget install RARLab.UnRAR) "
                    "or 7-Zip, or upload a .zip file instead."
                )
        except Exception as exc:
            if "unrar" in str(exc).lower() or "not found" in str(exc).lower():
                raise RuntimeError(
                    "Cannot extract .rar files: install 'unrar' (e.g. winget install RARLab.UnRAR) "
                    "or 7-Zip, or upload a .zip file instead."
                )
            raise
    elif lower.endswith(".7z"):
        import subprocess
        try:
            result = subprocess.run(
                ["7z", "x", archive_path, f"-o{dest}", "-y"],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr)
        except FileNotFoundError:
            raise RuntimeError(
                "Cannot extract .7z files: install 7-Zip (e.g. winget install 7zip.7zip) "
                "or upload a .zip file instead."
            )
    elif lower.endswith((".gz", ".bz2", ".xz")):
        import gzip
        import bz2
        import lzma
        openers = {".gz": gzip.open, ".bz2": bz2.open, ".xz": lzma.open}
        ext = Path(lower).suffix
        stem = Path(archive_path).stem
        with openers[ext](archive_path, "rb") as fin:
            out_path = dest / stem
            with open(out_path, "wb") as fout:
                shutil.copyfileobj(fin, fout)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")

    logger.info("archive.extract.done", dest=str(dest))
    return dest


def _stage_single_file(file_path: str, scan_id: UUID) -> Path:
    """Stage a single source file into a temp directory for analysis."""
    from config import settings

    dest = settings.clone_path / str(scan_id)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    src = Path(file_path)
    target = dest / src.name
    shutil.copy2(str(src), str(target))

    logger.info("file.staged", path=file_path, dest=str(dest))
    return dest
