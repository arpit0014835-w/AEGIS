""" 
AEGIS — Git Operations 
========================	
GitPython wrappers for repository cloning and file enumeration.	
""" 

from __future__ import annotations 

import shutil	
from pathlib import Path	
from uuid import UUID 

from git import Repo 
from git.exc import GitCommandError	

from config import settings	
from utils.logger import get_logger	

logger = get_logger(__name__) 

# File extensions we analyse 
SUPPORTED_EXTENSIONS: set[str] = { 
    # Python 
    ".py", ".pyw", ".pyi", ".ipynb", 
    # JavaScript / TypeScript	
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",	
    # JVM 
    ".java", ".kt", ".kts", ".scala", ".groovy", 
    # Systems	
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rs", ".go",	
    # Mobile 
    ".swift", ".dart", ".m", ".mm", 
    # Scripting	
    ".rb", ".php", ".lua", ".pl", ".r", ".R",	
    # Shell	
    ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd", 
    # Web / Markup 
    ".html", ".htm", ".css", ".scss", ".sass", ".less",	
    ".vue", ".svelte", 
    # Data / Config	
    ".json", ".yaml", ".yml", ".toml", ".xml", ".ini", ".cfg",	
    # Database 
    ".sql", 
    # Misc	
    ".md", ".rst", ".tf", ".hcl", ".dockerfile", 
}	

# Directories to skip 
SKIP_DIRS: set[str] = {	
    "node_modules", ".git", "__pycache__", ".venv", "venv",	
    "dist", "build", ".next", ".tox", ".eggs", 
    "vendor", "third_party", ".ipynb_checkpoints",
}	

# Max individual file size (500 KB) 
MAX_FILE_SIZE_BYTES: int = 500 * 1024 


def clone_repository(repo_url: str, scan_id: UUID) -> Path: 
    """	
    Clone a Git repository to a local directory.	

    Parameters 
    ---------- 
    repo_url : str	
        HTTPS URL of the repository. 
    scan_id : UUID	
        Unique scan identifier (used as the directory name). 

    Returns 
    -------	
    Path	
        Path to the cloned repository root. 

    Raises	
    ------	
    GitCommandError 
        If the clone fails (invalid URL, auth issues, etc.).
    """
    dest = settings.clone_path / str(scan_id)
    if dest.exists():
        shutil.rmtree(dest)

    logger.info("git.clone.start", repo_url=repo_url, dest=str(dest))
    try:
        Repo.clone_from(
            repo_url,
            str(dest),
            depth=1,          # Shallow clone for speed
            single_branch=True,
            no_checkout=False,
        )
        logger.info("git.clone.done", dest=str(dest))
        return dest
    except GitCommandError as exc:
        logger.error("git.clone.failed", repo_url=repo_url, error=str(exc))
        raise


def enumerate_source_files(root: Path) -> list[Path]:
    """
    Walk a directory tree and return paths to analysable source files.

    Skips vendor directories, hidden files, and files exceeding the size limit.
    """
    files: list[Path] = []

    for path in root.rglob("*"):
        # Skip directories in the exclusion set
        if any(part in SKIP_DIRS for part in path.parts):
            continue

        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            logger.warning("file.skipped.too_large", path=str(path))
            continue

        files.append(path)

    logger.info("files.enumerated", count=len(files), root=str(root))
    return files


def cleanup_clone(scan_id: UUID) -> None:
    """Remove the cloned repository directory."""
    dest = settings.clone_path / str(scan_id)
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
        logger.info("git.cleanup", dest=str(dest))
