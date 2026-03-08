""" 
AEGIS — Breach Secure Service 
================================	
AI-aware security scanning combining:	
  1. Semgrep with custom AI-focused rules 
  2. Pattern-based prompt injection detection 
  3. Optional Azure OpenAI semantic analysis	
  4. Optional Azure AI Content Safety jailbreak detection	
""" 

from __future__ import annotations 

import json	
import re	
import subprocess	
from pathlib import Path 
from typing import Optional 

from config import settings 
from models.enums import Severity, VulnerabilityCategory 
from models.report import BreachSecureResult, Vulnerability 
from utils.logger import get_logger	

logger = get_logger(__name__)	


# ─── Severity Weights for Scoring ─────────────────────────────────────────── 

_SEVERITY_PENALTY: dict[Severity, float] = { 
    Severity.CRITICAL: 25.0,	
    Severity.HIGH: 15.0,	
    Severity.MEDIUM: 8.0, 
    Severity.LOW: 3.0, 
    Severity.INFO: 1.0,	
}	


# ─── Built-in Pattern Rules ────────────────────────────────────────────────	
# Fallback when Semgrep is not installed. 

_BUILTIN_RULES: list[dict] = [ 
    {	
        "id": "aegis.prompt-injection-concat", 
        "pattern": re.compile(	
            r"""(?:f['\"]|\.format\(|%\s*\().*(?:user|input|query|prompt|message)""",	
            re.IGNORECASE, 
        ), 
        "category": VulnerabilityCategory.PROMPT_INJECTION,	
        "severity": Severity.HIGH, 
        "message": "User input appears to be directly concatenated into an LLM prompt without sanitization.",	
        "fix": "Use a prompt template with explicit input placeholders and validate/escape user input.", 
    },	
    {	
        "id": "aegis.hardcoded-api-key", 
        "pattern": re.compile( 
            r"""(?:api[_-]?key|secret|token|password)\s*[=:]\s*['\"][A-Za-z0-9+/=_-]{20,}['\"]""",	
            re.IGNORECASE, 
        ), 
        "category": VulnerabilityCategory.HARDCODED_SECRET, 
        "severity": Severity.CRITICAL,	
        "message": "Hardcoded API key or secret detected. This could be exposed in version control.",	
        "fix": "Move secrets to environment variables or a secure vault.", 
    }, 
    {	
        "id": "aegis.unvalidated-llm-response", 
        "pattern": re.compile(	
            r"""(?:\.execute|eval|exec)\s*\(\s*(?:response|result|output|completion)""", 
            re.IGNORECASE, 
        ),	
        "category": VulnerabilityCategory.UNVALIDATED_AI_OUTPUT,	
        "severity": Severity.CRITICAL, 
        "message": "LLM output is being executed without validation. This enables arbitrary code execution.",	
        "fix": "Never execute LLM outputs directly. Parse, validate, and sandbox before execution.",	
    }, 
    {
        "id": "aegis.missing-llm-error-handling",
        "pattern": re.compile(
            r"""(?:openai|anthropic|azure).*(?:create|complete|chat)\s*\(""",
            re.IGNORECASE,
        ),
        "category": VulnerabilityCategory.MISSING_ERROR_HANDLING,
        "severity": Severity.MEDIUM,
        "message": "LLM API call detected without visible error handling. Network failures or rate limits could crash the application.",
        "fix": "Wrap LLM calls in try/except blocks with retry logic and timeout handling.",
    },
    {
        "id": "aegis.insecure-llm-temperature",
        "pattern": re.compile(
            r"""temperature\s*[=:]\s*(?:1\.0|1|2)""",
            re.IGNORECASE,
        ),
        "category": VulnerabilityCategory.INSECURE_LLM_CALL,
        "severity": Severity.LOW,
        "message": "High temperature setting in LLM call increases output randomness, potentially causing unpredictable behavior in production.",
        "fix": "Use a lower temperature (0.0–0.3) for deterministic, production-ready outputs.",
    },
]


# ─── Semgrep Integration ───────────────────────────────────────────────────

def _run_semgrep(target_dir: str) -> list[Vulnerability]:
    """
    Run Semgrep with custom AI-focused rules.

    Falls back gracefully if Semgrep is not installed.
    """
    rules_dir = Path(settings.semgrep_rules_dir)
    if not rules_dir.exists():
        logger.warning("semgrep.rules_dir_missing", path=str(rules_dir))
        return []

    try:
        result = subprocess.run(
            [
                "semgrep",
                "--config", str(rules_dir),
                "--json",
                "--quiet",
                "--timeout", "30",
                target_dir,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode not in (0, 1):  # 1 = findings found
            logger.warning("semgrep.error", stderr=result.stderr[:500])
            return []

        data = json.loads(result.stdout) if result.stdout else {}
        findings = data.get("results", [])

        vulns: list[Vulnerability] = []
        for finding in findings:
            severity = _map_semgrep_severity(finding.get("extra", {}).get("severity", "WARNING"))
            category = _categorize_finding(finding.get("check_id", ""))

            vulns.append(Vulnerability(
                rule_id=finding.get("check_id", "unknown"),
                category=category,
                severity=severity,
                file_path=finding.get("path", ""),
                line_start=finding.get("start", {}).get("line", 0),
                line_end=finding.get("end", {}).get("line", 0),
                message=finding.get("extra", {}).get("message", ""),
                snippet=finding.get("extra", {}).get("lines", "")[:200],
            ))

        return vulns

    except FileNotFoundError:
        logger.info("semgrep.not_installed", msg="Falling back to built-in rules")
        return []
    except subprocess.TimeoutExpired:
        logger.warning("semgrep.timeout")
        return []
    except Exception as exc:
        logger.error("semgrep.unexpected_error", error=str(exc))
        return []


def _map_semgrep_severity(severity: str) -> Severity:
    """Map Semgrep severity strings to our enum."""
    mapping = {
        "ERROR": Severity.HIGH,
        "WARNING": Severity.MEDIUM,
        "INFO": Severity.LOW,
    }
    return mapping.get(severity.upper(), Severity.MEDIUM)


def _categorize_finding(check_id: str) -> VulnerabilityCategory:
    """Categorize a Semgrep finding based on rule ID."""
    check_lower = check_id.lower()
    if "prompt" in check_lower or "injection" in check_lower:
        return VulnerabilityCategory.PROMPT_INJECTION
    if "hallucin" in check_lower:
        return VulnerabilityCategory.HALLUCINATED_DEPENDENCY
    if "secret" in check_lower or "key" in check_lower:
        return VulnerabilityCategory.HARDCODED_SECRET
    if "llm" in check_lower or "ai" in check_lower:
        return VulnerabilityCategory.INSECURE_LLM_CALL
    return VulnerabilityCategory.UNVALIDATED_AI_OUTPUT


# ─── Built-in Pattern Scanning ──────────────────────────────────────────────

def _run_builtin_rules(source_files: list[Path]) -> list[Vulnerability]:
    """Scan files using built-in regex rules."""
    vulns: list[Vulnerability] = []

    for file_path in source_files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        lines = content.split("\n")
        for line_num, line in enumerate(lines, start=1):
            for rule in _BUILTIN_RULES:
                if rule["pattern"].search(line):
                    vulns.append(Vulnerability(
                        rule_id=rule["id"],
                        category=rule["category"],
                        severity=rule["severity"],
                        file_path=str(file_path),
                        line_start=line_num,
                        line_end=line_num,
                        message=rule["message"],
                        snippet=line.strip()[:200],
                        fix_suggestion=rule.get("fix"),
                    ))

    return vulns


# ─── Azure OpenAI Semantic Analysis (optional) ─────────────────────────────

async def _run_semantic_analysis(
    source_files: list[Path],
) -> list[Vulnerability]:
    """
    Use Azure OpenAI (GPT-4o) for deeper semantic vulnerability analysis.

    Only runs if Azure OpenAI credentials are configured.
    """
    if not settings.is_azure_openai_configured:
        logger.info("breach_secure.azure_openai.skipped", reason="not configured")
        return []

    try:
        from openai import AsyncAzureOpenAI

        client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )

        vulns: list[Vulnerability] = []

        # Analyse high-risk files (those with LLM-related code)
        for file_path in source_files[:10]:  # Limit to avoid cost explosion
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # Only analyse files with AI/LLM-related keywords
            if not any(kw in content.lower() for kw in ["openai", "llm", "prompt", "gpt", "anthropic", "langchain"]):
                continue

            response = await client.chat.completions.create(
                model=settings.azure_openai_deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a security auditor specializing in AI/LLM application security. "
                            "Analyse the following code for: prompt injection vulnerabilities, "
                            "insecure LLM API usage, unvalidated AI outputs, and jailbreak risks. "
                            "Return findings as JSON array with keys: line, severity (critical/high/medium/low), "
                            "category, message, fix."
                        ),
                    },
                    {"role": "user", "content": content[:4000]},
                ],
                temperature=0.1,
                max_tokens=1000,
            )

            # Parse response
            resp_text = response.choices[0].message.content or ""
            try:
                findings = json.loads(resp_text)
                if isinstance(findings, list):
                    for f in findings:
                        vulns.append(Vulnerability(
                            rule_id=f"aegis.semantic.{f.get('category', 'unknown')}",
                            category=VulnerabilityCategory(f.get("category", "insecure_llm_call")),
                            severity=Severity(f.get("severity", "medium")),
                            file_path=str(file_path),
                            line_start=f.get("line", 0),
                            line_end=f.get("line", 0),
                            message=f.get("message", ""),
                            fix_suggestion=f.get("fix"),
                        ))
            except (json.JSONDecodeError, ValueError):
                logger.warning("azure_openai.parse_failed", file=str(file_path))

        return vulns

    except ImportError:
        logger.warning("openai.not_installed")
        return []
    except Exception as exc:
        logger.error("azure_openai.error", error=str(exc))
        return []


# ─── Public API ──────────────────────────────────────────────────────────────

async def run_breach_secure(
    source_files: list[Path],
    target_dir: str,
) -> BreachSecureResult:
    """
    Execute the Breach Secure analysis pipeline.

    Steps:
    1. Run Semgrep with custom AI-focused rules
    2. Run built-in regex pattern rules
    3. Optionally run Azure OpenAI semantic analysis
    4. Deduplicate and score
    """
    logger.info("breach_secure.start", file_count=len(source_files))

    # Collect vulnerabilities from all sources
    all_vulns: list[Vulnerability] = []

    # Semgrep
    semgrep_vulns = _run_semgrep(target_dir)
    all_vulns.extend(semgrep_vulns)

    # Built-in rules
    builtin_vulns = _run_builtin_rules(source_files)
    all_vulns.extend(builtin_vulns)

    # Azure OpenAI (optional)
    semantic_vulns = await _run_semantic_analysis(source_files)
    all_vulns.extend(semantic_vulns)

    # Deduplicate by (file, line, rule)
    seen: set[tuple[str, int, str]] = set()
    unique_vulns: list[Vulnerability] = []
    for v in all_vulns:
        key = (v.file_path, v.line_start, v.rule_id)
        if key not in seen:
            seen.add(key)
            unique_vulns.append(v)

    # Count by severity
    counts = {s: 0 for s in Severity}
    for v in unique_vulns:
        counts[v.severity] += 1

    # Score calculation (100 = clean)
    total_penalty = sum(
        counts[s] * _SEVERITY_PENALTY[s] for s in Severity
    )
    score = max(0.0, 100.0 - total_penalty)

    result = BreachSecureResult(
        vulnerabilities=unique_vulns,
        critical_count=counts[Severity.CRITICAL],
        high_count=counts[Severity.HIGH],
        medium_count=counts[Severity.MEDIUM],
        low_count=counts[Severity.LOW],
        info_count=counts[Severity.INFO],
        score=round(score, 2),
    )

    logger.info(
        "breach_secure.complete",
        score=result.score,
        total_vulns=len(unique_vulns),
        critical=result.critical_count,
        high=result.high_count,
    )
    return result
