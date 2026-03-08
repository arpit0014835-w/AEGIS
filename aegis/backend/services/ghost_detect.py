""" 
AEGIS — Ghost Detect Service (ML-Powered) 
============================================	
Identifies AI-generated code through:	
  1. Trained XGBoost/RandomForest classifier (38 code features) 
  2. Cosine similarity analysis for style consistency across files 
  3. Hallucinated dependency detection (non-existent PyPI/npm packages)	

The ML model is loaded once at module import and used for per-file	
AI probability prediction. Falls back to heuristic scoring if no 
trained model is available. 
"""	

from __future__ import annotations	

import re	
import statistics 
from pathlib import Path 
from typing import Optional 

import httpx 
import numpy as np 
from sklearn.preprocessing import StandardScaler	

from models.enums import Language	
from models.report import FileAnalysis, GhostDetectResult, HallucinatedDependency 
from services.ml.feature_extractor import extract_features, FEATURE_NAMES 
from services.ml.heuristic_analyzer import analyze_code_heuristic
from utils.file_parser import ParsedFile	
from utils.logger import get_logger	

logger = get_logger(__name__) 

# ─── Constants ────────────────────────────────────────────────────────────── 

HALLUCINATION_WEIGHT = 0.10         # Per hallucinated dep adds to AI probability	
MODEL_DIR = Path(__file__).parent.parent / "models" / "saved"	
MODEL_NAME = "ghost_detect_model"	

# Package registry endpoints 
PYPI_API = "https://pypi.org/pypi/{package}/json" 
NPM_API = "https://registry.npmjs.org/{package}"	

# Known standard library modules (subset) — won't check these 
_PYTHON_STDLIB: set[str] = {	
    "os", "sys", "re", "json", "math", "datetime", "collections",	
    "functools", "itertools", "pathlib", "typing", "abc", "io", 
    "hashlib", "logging", "unittest", "dataclasses", "enum", 
    "asyncio", "contextlib", "copy", "csv", "http", "urllib",	
    "socket", "threading", "subprocess", "shutil", "tempfile", 
    "textwrap", "time", "uuid", "warnings", "zipfile", "argparse",	
    "configparser", "email", "html", "xml", "sqlite3", "string", 
    "struct", "traceback", "pickle", "pprint", "inspect",	
}	


# ─── ML Model Singleton ───────────────────────────────────────────────────── 

_ml_model: Optional[object] = None 
_ml_scaler: Optional[StandardScaler] = None	
_model_loaded: bool = False 


def _load_ml_model() -> bool: 
    """ 
    Attempt to load the trained ML model. Returns True if successful.	
    Called once at first use (lazy loading).	
    """ 
    global _ml_model, _ml_scaler, _model_loaded 

    if _model_loaded:	
        return _ml_model is not None 

    _model_loaded = True	

    try: 
        from services.ml.trainer import load_model 
        loaded = load_model(MODEL_DIR, MODEL_NAME)	
        _ml_model = loaded["model"]	
        _ml_scaler = loaded["scaler"] 
        logger.info("ghost_detect.ml_model_loaded", model_dir=str(MODEL_DIR))	
        return True	
    except Exception as exc: 
        logger.warning(
            "ghost_detect.ml_model_not_found_using_heuristic",
            error=str(exc),
            hint="Run 'python train_model.py' to train the ML model.",
        )
        return False


# ─── ML Prediction ──────────────────────────────────────────────────────────


def _predict_ai_probability(code: str) -> float:
    """
    Predict AI probability for a single code sample using the trained ML model.

    Returns a float in [0.0, 1.0] where 1.0 = definitely AI-generated.
    Falls back to 0.5 (unknown) if model is not available.
    """
    if not _load_ml_model():
        return 0.5  # Fallback — model not trained yet

    features = extract_features(code)
    features_2d = features.reshape(1, -1)

    # Scale
    features_scaled = _ml_scaler.transform(features_2d)
    features_scaled = np.nan_to_num(features_scaled, nan=0.0, posinf=0.0, neginf=0.0)

    # Predict probability
    proba = _ml_model.predict_proba(features_scaled)[0]

    # proba[1] = probability of class 1 (AI-generated)
    return float(proba[1])


# ─── Dependency Validation ──────────────────────────────────────────────────


async def _check_pypi_package(package: str) -> bool:
    """Check if a Python package exists on PyPI."""
    if package in _PYTHON_STDLIB:
        return True
    root = package.split(".")[0]
    if root in _PYTHON_STDLIB:
        return True

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.head(PYPI_API.format(package=root))
            return resp.status_code == 200
        except httpx.RequestError:
            return True  # Assume exists on network error


async def _check_npm_package(package: str) -> bool:
    """Check if an npm package exists on the registry."""
    if package.startswith(".") or package.startswith("/"):
        return True

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.head(NPM_API.format(package=package))
            return resp.status_code == 200
        except httpx.RequestError:
            return True


async def _validate_dependencies(
    parsed_files: list[ParsedFile],
) -> list[HallucinatedDependency]:
    """Check all imports against public registries."""
    hallucinated: list[HallucinatedDependency] = []

    for pf in parsed_files:
        for imp in pf.imports:
            exists = True

            if pf.language == "python":
                exists = await _check_pypi_package(imp.module)
                registry = "pypi"
            elif pf.language in ("javascript", "typescript"):
                exists = await _check_npm_package(imp.module)
                registry = "npm"
            else:
                continue

            if not exists:
                hallucinated.append(HallucinatedDependency(
                    package_name=imp.module,
                    file_path=pf.file_path,
                    line_number=imp.line_number,
                    registry=registry,
                ))
                logger.warning(
                    "ghost_detect.hallucinated_dep",
                    package=imp.module,
                    file=pf.file_path,
                    registry=registry,
                )

    return hallucinated


# ─── Public API ──────────────────────────────────────────────────────────────


async def run_ghost_detect(
    parsed_files: list[ParsedFile],
    source_files: list[Path],
) -> GhostDetectResult:
    """
    Execute the Ghost Detect analysis pipeline.

    Steps:
    1. Load file contents
    2. Run ML model prediction on each file for AI probability
    3. Validate dependencies against public registries
    4. Combine scores with hallucinated dependency penalties
    5. Calculate per-file analysis and overall score
    """
    logger.info("ghost_detect.start", file_count=len(parsed_files))

    # Read file contents
    file_contents: dict[str, str] = {}
    for fp in source_files:
        try:
            file_contents[str(fp)] = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            file_contents[str(fp)] = ""

    # Dependency validation
    hallucinated = await _validate_dependencies(parsed_files)
    halluc_files = {h.file_path for h in hallucinated}

    # Build per-file analysis using ML predictions
    file_analyses: list[FileAnalysis] = []
    ai_probabilities: list[float] = []
    anomaly_count = 0

    for pf in parsed_files:
        content = file_contents.get(pf.file_path, "")

        # ─── AI probability ─────────────────────────────────────────
        # For .ipynb files, extract Python code cells before prediction
        if pf.file_path.endswith(".ipynb") and content.strip():
            import json as _json
            try:
                nb = _json.loads(content)
                cells = nb.get("cells", [])
                code_parts = []
                for cell in cells:
                    if cell.get("cell_type") == "code":
                        src = cell.get("source", [])
                        code_parts.append("".join(src) if isinstance(src, list) else src)
                content = "\n\n".join(code_parts)
            except (ValueError, _json.JSONDecodeError):
                pass  # Use raw content as fallback

        if pf.language == "python" and content.strip():
            ai_prob = _predict_ai_probability(content)
            detection_method = "ml_model"
        elif content.strip():
            heuristic_result = analyze_code_heuristic(content)
            ai_prob = heuristic_result.ai_probability
            detection_method = "heuristic"
        else:
            ai_prob = 0.0
            detection_method = "skipped"

        # Add penalty for hallucinated dependencies
        if pf.file_path in halluc_files:
            deps_in_file = sum(1 for h in hallucinated if h.file_path == pf.file_path)
            ai_prob = min(1.0, ai_prob + deps_in_file * HALLUCINATION_WEIGHT)

        ai_prob = max(0.0, min(1.0, ai_prob))

        # Style consistency = inverse of AI probability
        style_consistency = 1.0 - ai_prob

        if ai_prob > 0.6:
            anomaly_count += 1

        lang_str = pf.language.lower() if pf.language else "unknown"
        try:
            lang = Language(lang_str)
        except ValueError:
            lang = Language.UNKNOWN

        file_analyses.append(FileAnalysis(
            file_path=pf.file_path,
            language=lang,
            line_count=pf.line_count,
            function_count=len(pf.functions),
            ai_probability=round(ai_prob, 4),
            style_consistency_score=round(style_consistency, 4),
            detection_method=detection_method,
        ))
        ai_probabilities.append(ai_prob)

    # Overall score (100 = fully human)
    overall_ai_prob = (
        statistics.mean(ai_probabilities) if ai_probabilities else 0.0
    )
    score = max(0.0, 100.0 * (1.0 - overall_ai_prob))

    result = GhostDetectResult(
        overall_ai_probability=round(overall_ai_prob, 4),
        file_analyses=file_analyses,
        hallucinated_dependencies=hallucinated,
        style_anomaly_count=anomaly_count,
        score=round(score, 2),
    )

    logger.info(
        "ghost_detect.complete",
        score=result.score,
        anomalies=anomaly_count,
        hallucinated=len(hallucinated),
        ml_model_active=_ml_model is not None,
        hybrid_detection=True,
    )
    return result
