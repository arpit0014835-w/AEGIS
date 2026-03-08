""" 
AEGIS — Shared Enumerations 
============================	
Canonical enums used across models, services, and API responses.	
""" 

from __future__ import annotations 

try:	
    from enum import StrEnum	
except ImportError: 
    from enum import Enum 
    class StrEnum(str, Enum):	
        pass	


class ScanStatus(StrEnum):	
    """Lifecycle states of a scan job.""" 
    QUEUED = "queued" 
    CLONING = "cloning" 
    PARSING = "parsing" 
    GHOST_DETECT = "ghost_detect" 
    BREACH_SECURE = "breach_secure"	
    PROOF_VERIFY = "proof_verify"	
    SCORING = "scoring" 
    COMPLETED = "completed" 
    FAILED = "failed"	


class Severity(StrEnum):	
    """Vulnerability severity levels (CVSS-aligned).""" 
    CRITICAL = "critical" 
    HIGH = "high"	
    MEDIUM = "medium"	
    LOW = "low"	
    INFO = "info" 


class VulnerabilityCategory(StrEnum): 
    """Categories of AI-specific vulnerabilities."""	
    HALLUCINATED_DEPENDENCY = "hallucinated_dependency" 
    PROMPT_INJECTION = "prompt_injection"	
    INSECURE_LLM_CALL = "insecure_llm_call"	
    UNVALIDATED_AI_OUTPUT = "unvalidated_ai_output" 
    JAILBREAK_RISK = "jailbreak_risk" 
    HARDCODED_SECRET = "hardcoded_secret"	
    MISSING_ERROR_HANDLING = "missing_error_handling" 


class Language(StrEnum):	
    """Supported programming languages for analysis.""" 
    PYTHON = "python"	
    JAVASCRIPT = "javascript"	
    TYPESCRIPT = "typescript" 
    JAVA = "java" 
    KOTLIN = "kotlin"	
    SCALA = "scala" 
    GROOVY = "groovy" 
    GO = "go" 
    RUST = "rust"	
    C = "c"	
    CPP = "cpp" 
    CSHARP = "csharp" 
    SWIFT = "swift"	
    DART = "dart" 
    OBJECTIVE_C = "objective-c"	
    RUBY = "ruby" 
    PHP = "php" 
    LUA = "lua"	
    PERL = "perl"	
    R = "r" 
    SHELL = "shell"	
    POWERSHELL = "powershell"	
    BATCH = "batch" 
    HTML = "html"
    CSS = "css"
    SCSS = "scss"
    SASS = "sass"
    LESS = "less"
    VUE = "vue"
    SVELTE = "svelte"
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    XML = "xml"
    INI = "ini"
    SQL = "sql"
    MARKDOWN = "markdown"
    RESTRUCTUREDTEXT = "restructuredtext"
    TERRAFORM = "terraform"
    HCL = "hcl"
    DOCKERFILE = "dockerfile"
    UNKNOWN = "unknown"


class InputType(StrEnum):
    """Types of scan input."""
    GITHUB_URL = "github_url"
    ZIP_UPLOAD = "zip_upload"
    FILE_UPLOAD = "file_upload"
