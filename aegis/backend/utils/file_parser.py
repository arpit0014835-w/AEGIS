""" 
AEGIS — File Parser (Tree-sitter AST Extraction) 
===================================================	
Parse source files into structured representations using Tree-sitter.	
Extracts function/class definitions, imports, and structural metadata. 
""" 

from __future__ import annotations	

import json
import re	
from dataclasses import dataclass, field 
from pathlib import Path 
from typing import Optional	

from utils.logger import get_logger	

logger = get_logger(__name__)	


# ─── Data Structures ──────────────────────────────────────────────────────── 

@dataclass 
class FunctionDef: 
    """Extracted function definition.""" 
    name: str 
    start_line: int	
    end_line: int	
    parameter_count: int = 0 
    has_docstring: bool = False 
    body_line_count: int = 0	


@dataclass	
class ImportStatement: 
    """Extracted import statement.""" 
    module: str	
    alias: Optional[str] = None	
    line_number: int = 0	
    is_from_import: bool = False 


@dataclass 
class ParsedFile:	
    """Structured representation of a parsed source file.""" 
    file_path: str	
    language: str = "unknown"	
    line_count: int = 0 
    functions: list[FunctionDef] = field(default_factory=list) 
    imports: list[ImportStatement] = field(default_factory=list)	
    class_count: int = 0 
    comment_lines: int = 0	
    blank_lines: int = 0 
    avg_line_length: float = 0.0	
    max_line_length: int = 0	
    has_type_hints: bool = False 


# ─── Language Detection ────────────────────────────────────────────────────── 

EXTENSION_TO_LANGUAGE: dict[str, str] = {	
    # Python 
    ".py": "python", ".pyw": "python", ".pyi": "python", ".ipynb": "python", 
    # JavaScript / TypeScript 
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",	
    ".ts": "typescript", ".tsx": "typescript",	
    # JVM 
    ".java": "java", ".kt": "kotlin", ".kts": "kotlin", 
    ".scala": "scala", ".groovy": "groovy",	
    # Systems 
    ".go": "go", ".rs": "rust",	
    ".c": "c", ".h": "c", 
    ".cpp": "cpp", ".hpp": "cpp", 
    ".cs": "csharp",	
    # Mobile	
    ".swift": "swift", ".dart": "dart", 
    ".m": "objective-c", ".mm": "objective-c",	
    # Scripting	
    ".rb": "ruby", ".php": "php", ".lua": "lua", 
    ".pl": "perl", ".r": "r", ".R": "r",
    # Shell
    ".sh": "shell", ".bash": "shell", ".zsh": "shell",
    ".ps1": "powershell", ".bat": "batch", ".cmd": "batch",
    # Web / Markup
    ".html": "html", ".htm": "html",
    ".css": "css", ".scss": "scss", ".sass": "sass", ".less": "less",
    ".vue": "vue", ".svelte": "svelte",
    # Data / Config
    ".json": "json", ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml", ".xml": "xml", ".ini": "ini", ".cfg": "ini",
    # Database
    ".sql": "sql",
    # Misc
    ".md": "markdown", ".rst": "restructuredtext",
    ".tf": "terraform", ".hcl": "hcl", ".dockerfile": "dockerfile",
}


def detect_language(file_path: Path) -> str:
    """Determine programming language from file extension."""
    return EXTENSION_TO_LANGUAGE.get(file_path.suffix.lower(), "unknown")


# ─── Regex-Based Parsers (Fallback when Tree-sitter unavailable) ─────────

# Python patterns
_PY_FUNC = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)", re.MULTILINE)
_PY_CLASS = re.compile(r"^\s*class\s+(\w+)", re.MULTILINE)
_PY_IMPORT = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+)?import\s+([\w., ]+)", re.MULTILINE
)
_PY_COMMENT = re.compile(r"^\s*#", re.MULTILINE)

# JavaScript / TypeScript patterns
_JS_FUNC = re.compile(
    r"(?:(?:async\s+)?function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\()",
    re.MULTILINE,
)
_JS_CLASS = re.compile(r"^\s*(?:export\s+)?class\s+(\w+)", re.MULTILINE)
_JS_IMPORT = re.compile(
    r"""^\s*import\s+(?:\{[^}]+\}\s+from\s+|[\w]+\s+from\s+)?['"]([^'"]+)['"]""",
    re.MULTILINE,
)
_JS_COMMENT = re.compile(r"^\s*(?://|/\*|\*)", re.MULTILINE)


def _parse_python(content: str, file_path: str) -> ParsedFile:
    """Parse a Python file using regex patterns."""
    lines = content.split("\n")
    parsed = ParsedFile(
        file_path=file_path,
        language="python",
        line_count=len(lines),
    )

    # Functions
    for match in _PY_FUNC.finditer(content):
        params = match.group(2).strip()
        param_count = len([p for p in params.split(",") if p.strip()]) if params else 0
        line_num = content[:match.start()].count("\n") + 1
        parsed.functions.append(FunctionDef(
            name=match.group(1),
            start_line=line_num,
            end_line=line_num,  # Approximate
            parameter_count=param_count,
        ))

    # Classes
    parsed.class_count = len(_PY_CLASS.findall(content))

    # Imports
    for match in _PY_IMPORT.finditer(content):
        line_num = content[:match.start()].count("\n") + 1
        from_module = match.group(1)
        imports = match.group(2)
        if from_module:
            parsed.imports.append(ImportStatement(
                module=from_module,
                line_number=line_num,
                is_from_import=True,
            ))
        else:
            for imp in imports.split(","):
                imp = imp.strip().split(" as ")[0].strip()
                if imp:
                    parsed.imports.append(ImportStatement(
                        module=imp,
                        line_number=line_num,
                    ))

    # Metrics
    parsed.comment_lines = len(_PY_COMMENT.findall(content))
    parsed.blank_lines = sum(1 for line in lines if not line.strip())
    line_lengths = [len(line) for line in lines if line.strip()]
    if line_lengths:
        parsed.avg_line_length = sum(line_lengths) / len(line_lengths)
        parsed.max_line_length = max(line_lengths)
    parsed.has_type_hints = bool(re.search(r":\s*\w+|->", content))

    return parsed


def _parse_javascript(content: str, file_path: str) -> ParsedFile:
    """Parse a JavaScript/TypeScript file using regex patterns."""
    lines = content.split("\n")
    parsed = ParsedFile(
        file_path=file_path,
        language="javascript" if file_path.endswith((".js", ".jsx")) else "typescript",
        line_count=len(lines),
    )

    # Functions
    for match in _JS_FUNC.finditer(content):
        name = match.group(1) or match.group(2) or "anonymous"
        line_num = content[:match.start()].count("\n") + 1
        parsed.functions.append(FunctionDef(
            name=name,
            start_line=line_num,
            end_line=line_num,
        ))

    # Classes
    parsed.class_count = len(_JS_CLASS.findall(content))

    # Imports
    for match in _JS_IMPORT.finditer(content):
        line_num = content[:match.start()].count("\n") + 1
        parsed.imports.append(ImportStatement(
            module=match.group(1),
            line_number=line_num,
        ))

    # Metrics
    parsed.comment_lines = len(_JS_COMMENT.findall(content))
    parsed.blank_lines = sum(1 for line in lines if not line.strip())
    line_lengths = [len(line) for line in lines if line.strip()]
    if line_lengths:
        parsed.avg_line_length = sum(line_lengths) / len(line_lengths)
        parsed.max_line_length = max(line_lengths)

    return parsed


# ─── Public API ──────────────────────────────────────────────────────────────

def _extract_notebook_python(raw: str) -> str:
    """Extract Python source code from a Jupyter .ipynb notebook JSON."""
    try:
        nb = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw  # Fallback: treat as plain text

    cells = nb.get("cells", [])
    code_parts: list[str] = []
    for cell in cells:
        if cell.get("cell_type") == "code":
            source = cell.get("source", [])
            if isinstance(source, list):
                code_parts.append("".join(source))
            elif isinstance(source, str):
                code_parts.append(source)
    return "\n\n".join(code_parts)


def parse_file(file_path: Path) -> ParsedFile:
    """
    Parse a source file and return structured metadata.

    Uses regex-based parsing as a robust fallback.
    For production Tree-sitter integration, swap in the AST-based parsers.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        logger.warning("parse.read_failed", path=str(file_path), error=str(exc))
        return ParsedFile(file_path=str(file_path))

    language = detect_language(file_path)

    # Extract Python code cells from Jupyter notebooks
    if file_path.suffix.lower() == ".ipynb":
        content = _extract_notebook_python(content)

    if language == "python":
        return _parse_python(content, str(file_path))
    elif language in ("javascript", "typescript"):
        return _parse_javascript(content, str(file_path))
    else:
        # Generic line metrics
        lines = content.split("\n")
        line_lengths = [len(line) for line in lines if line.strip()]
        return ParsedFile(
            file_path=str(file_path),
            language=language,
            line_count=len(lines),
            blank_lines=sum(1 for line in lines if not line.strip()),
            avg_line_length=(sum(line_lengths) / len(line_lengths)) if line_lengths else 0,
            max_line_length=max(line_lengths) if line_lengths else 0,
        )


def parse_codebase(files: list[Path]) -> list[ParsedFile]:
    """Parse all source files in a codebase."""
    results: list[ParsedFile] = []
    for f in files:
        parsed = parse_file(f)
        results.append(parsed)
    logger.info("codebase.parsed", total=len(results))
    return results
