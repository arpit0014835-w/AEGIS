"""
AEGIS — Heuristic AI-Code Detector (Language-Agnostic)
=======================================================
Multi-signal heuristic analyzer for detecting AI-generated code in non-Python
files where no trained ML model is available.

Signals used:
  1. Stylometric uniformity (AI code is unnaturally consistent)
  2. Comment pattern analysis (AI has distinctive commenting style)
  3. Naming convention analysis (AI uses overly descriptive names)
  4. Entropy & repetition (AI has lower uniqueness, more repetition)
  5. Structural regularity (AI produces very regular code structure)
"""

from __future__ import annotations

import math
import re
import statistics
from collections import Counter
from dataclasses import dataclass


@dataclass
class HeuristicResult:
    """Result from the heuristic AI-code detector."""
    ai_probability: float
    signals: dict[str, float]
    detection_method: str = "heuristic"


# ─── Signal Weights ──────────────────────────────────────────────────────────

_SIGNAL_WEIGHTS: dict[str, float] = {
    "line_length_uniformity": 0.15,
    "comment_pattern": 0.20,
    "naming_regularity": 0.15,
    "entropy_signal": 0.15,
    "structural_regularity": 0.15,
    "boilerplate_ratio": 0.10,
    "docstring_density": 0.10,
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _safe_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def _shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counter = Counter(text)
    total = len(text)
    return -sum((c / total) * math.log2(c / total) for c in counter.values() if c > 0)


# ─── Signal Extractors ──────────────────────────────────────────────────────


def _line_length_uniformity(lines: list[str]) -> float:
    """
    AI-generated code tends to have very uniform line lengths.
    Returns a score 0.0 (human-like variance) to 1.0 (AI-like uniformity).
    """
    non_empty = [len(l) for l in lines if l.strip()]
    if len(non_empty) < 5:
        return 0.5  # Not enough data

    std = _safe_std([float(x) for x in non_empty])
    mean = statistics.mean(non_empty)
    if mean == 0:
        return 0.5

    cv = std / mean  # coefficient of variation

    # Human code: CV typically 0.5-1.0+, AI code: CV typically 0.2-0.5
    if cv < 0.25:
        return 0.85
    elif cv < 0.40:
        return 0.65
    elif cv < 0.55:
        return 0.45
    elif cv < 0.70:
        return 0.30
    else:
        return 0.15


def _comment_pattern_signal(code: str, lines: list[str]) -> float:
    """
    AI code has distinctive comment patterns:
    - Section dividers (# ─── Section ───)
    - Overly descriptive inline comments
    - Comments on nearly every block
    - Step-by-step numbered comments
    """
    if not lines:
        return 0.5

    total = len(lines)
    score = 0.0
    signals = 0

    # Check for section divider comments (very AI-like)
    divider_re = re.compile(r'[#/]\s*[-─═=]{3,}')
    divider_count = sum(1 for l in lines if divider_re.search(l))
    if divider_count > 0:
        score += min(1.0, divider_count / max(total * 0.02, 1)) * 0.8
        signals += 1

    # Check for step-by-step comments (Step 1:, Step 2:, etc.)
    step_re = re.compile(r'[#/]{1,2}\s*(?:Step|Phase|Stage)\s*\d', re.IGNORECASE)
    step_count = sum(1 for l in lines if step_re.search(l))
    if step_count >= 2:
        score += 0.7
        signals += 1

    # Check comment density — AI typically comments 15-30% of lines
    comment_lines = sum(1 for l in lines if l.strip().startswith(('#', '//', '/*', '*')))
    comment_ratio = comment_lines / max(total, 1)
    if 0.12 < comment_ratio < 0.35:
        score += 0.5
        signals += 1
    elif comment_ratio > 0.35:
        score += 0.3
        signals += 1

    # Check for overly descriptive comments
    desc_re = re.compile(
        r'[#/]{1,2}\s*(?:This function|This method|This class|Initialize|'
        r'Create|Return|Check if|Validate|Ensure|Handle|Process)',
        re.IGNORECASE,
    )
    desc_count = sum(1 for l in lines if desc_re.search(l))
    if desc_count >= 3:
        score += min(1.0, desc_count / 5) * 0.6
        signals += 1

    return min(1.0, score / max(signals, 1)) if signals > 0 else 0.3


def _naming_regularity_signal(code: str) -> float:
    """
    AI tends to use very regular, descriptive naming conventions:
    - camelCase or snake_case consistently
    - Long, descriptive names (e.g., processUserInput vs proc)
    - Very few single-char variables
    """
    # Extract identifiers (simplified regex approach for any language)
    ident_re = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]{1,})\b')
    # Filter out common keywords
    common_kw = {
        'if', 'else', 'for', 'while', 'return', 'function', 'class', 'def',
        'var', 'let', 'const', 'new', 'this', 'self', 'import', 'from',
        'export', 'default', 'true', 'false', 'null', 'undefined', 'None',
        'True', 'False', 'try', 'catch', 'except', 'finally', 'throw',
        'raise', 'async', 'await', 'yield', 'break', 'continue', 'switch',
        'case', 'public', 'private', 'protected', 'static', 'void', 'int',
        'string', 'bool', 'float', 'double', 'long', 'char', 'byte',
        'extends', 'implements', 'interface', 'abstract', 'final', 'override',
        'package', 'struct', 'enum', 'type', 'typeof', 'instanceof',
    }

    identifiers = [m for m in ident_re.findall(code) if m not in common_kw]
    if len(identifiers) < 10:
        return 0.5  # Not enough data

    # Average identifier length — AI tends toward 8-20 chars
    lengths = [len(i) for i in identifiers]
    avg_len = statistics.mean(lengths)

    # Single-char ratio — AI rarely uses single-char names
    single_char = sum(1 for i in identifiers if len(i) <= 2) / len(identifiers)

    # Snake_case ratio
    snake = sum(1 for i in identifiers if '_' in i and i == i.lower()) / len(identifiers)
    # camelCase ratio
    camel = sum(1 for i in identifiers if re.match(r'^[a-z]+[A-Z]', i)) / len(identifiers)

    # Naming consistency (high = AI-like)
    dominant_convention = max(snake, camel)

    score = 0.0

    # Long, descriptive names signal AI
    if avg_len > 10:
        score += 0.7
    elif avg_len > 7:
        score += 0.5
    elif avg_len > 5:
        score += 0.3

    # Low single-char ratio signals AI
    if single_char < 0.05:
        score += 0.6
    elif single_char < 0.15:
        score += 0.3

    # High naming consistency signals AI
    if dominant_convention > 0.6:
        score += 0.5
    elif dominant_convention > 0.4:
        score += 0.3

    return min(1.0, score / 1.8)  # Normalize


def _entropy_signal(code: str, lines: list[str]) -> float:
    """
    AI code tends to have lower token-level entropy (more predictable patterns).
    Human code is often messier with varied patterns.
    """
    if len(code) < 100:
        return 0.5

    # Character-level entropy
    char_entropy = _shannon_entropy(code)

    # Token repetition — extract words
    tokens = re.findall(r'\b\w+\b', code)
    if not tokens:
        return 0.5

    unique_ratio = len(set(tokens)) / len(tokens)

    # Bigram repetition
    bigrams = [(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)] if len(tokens) >= 2 else []
    bigram_counter = Counter(bigrams)
    repeated_bigrams = sum(c for c in bigram_counter.values() if c > 1)
    bigram_repetition = repeated_bigrams / max(len(bigrams), 1)

    score = 0.0

    # Lower unique ratio = more repetitive = more AI-like
    if unique_ratio < 0.30:
        score += 0.7
    elif unique_ratio < 0.45:
        score += 0.5
    elif unique_ratio < 0.55:
        score += 0.3

    # Higher bigram repetition = more AI-like
    if bigram_repetition > 0.5:
        score += 0.6
    elif bigram_repetition > 0.3:
        score += 0.4
    elif bigram_repetition > 0.15:
        score += 0.2

    # Moderate char entropy is typical for AI (too high = random, too low = trivial)
    if 3.5 < char_entropy < 5.0:
        score += 0.3

    return min(1.0, score / 1.6)


def _structural_regularity_signal(lines: list[str]) -> float:
    """
    AI code tends to have very regular structure:
    - Consistent indentation patterns
    - Balanced blocks (similar function sizes)
    - Regular spacing between sections
    """
    if len(lines) < 10:
        return 0.5

    non_empty = [l for l in lines if l.strip()]
    if len(non_empty) < 5:
        return 0.5

    # Indentation consistency
    indents = []
    for l in non_empty:
        stripped = l.lstrip()
        indent = len(l) - len(stripped)
        indents.append(indent)

    indent_std = _safe_std([float(i) for i in indents])
    indent_mean = statistics.mean(indents) if indents else 0

    # Blank line spacing regularity
    blank_positions = [i for i, l in enumerate(lines) if not l.strip()]
    if len(blank_positions) >= 3:
        gaps = [blank_positions[i + 1] - blank_positions[i] for i in range(len(blank_positions) - 1)]
        gap_std = _safe_std([float(g) for g in gaps])
        gap_regularity = 1.0 / (1.0 + gap_std)  # Higher = more regular
    else:
        gap_regularity = 0.5

    score = 0.0

    # Regular blank line spacing signals AI
    if gap_regularity > 0.3:
        score += 0.5
    elif gap_regularity > 0.15:
        score += 0.3

    # Moderate, consistent indentation signals AI
    if indent_std < 3.0 and indent_mean > 1.0:
        score += 0.5
    elif indent_std < 5.0:
        score += 0.3

    return min(1.0, score / 1.0)


def _boilerplate_ratio_signal(code: str) -> float:
    """
    AI code often includes common boilerplate patterns:
    - Error handling templates
    - Import grouping
    - Constructor patterns
    """
    patterns = [
        r'try\s*\{[\s\S]*?\}\s*catch',      # try-catch blocks
        r'if\s*\(.*?===?\s*null',             # null checks
        r'(?:console\.log|print|logger)',     # logging
        r'(?:TODO|FIXME|HACK|NOTE):',         # TODO comments
        r'(?:@param|@returns?|@throws)',       # JSDoc
        r'(?:Args:|Returns:|Raises:)',         # Python docstring sections
        r'(?:export\s+default|module\.exports)', # Module exports
    ]

    match_count = sum(1 for p in patterns if re.search(p, code, re.IGNORECASE))
    ratio = match_count / len(patterns)

    if ratio > 0.5:
        return 0.7
    elif ratio > 0.3:
        return 0.5
    elif ratio > 0.15:
        return 0.35
    return 0.2


def _docstring_density_signal(code: str, lines: list[str]) -> float:
    """
    AI code tends to have thorough documentation:
    - Docstrings on every function
    - Type annotations
    - Parameter descriptions
    """
    total = max(len(lines), 1)

    # Multi-line comment/docstring blocks
    triple_quote = len(re.findall(r'"""', code)) + len(re.findall(r"'''", code))
    jsdoc = len(re.findall(r'/\*\*', code))
    doc_blocks = triple_quote // 2 + jsdoc

    # Type annotations (generic across languages)
    type_hints = len(re.findall(
        r':\s*(?:str|int|float|bool|list|dict|Optional|List|Dict|Tuple|'
        r'string|number|boolean|Array|Record|Promise|void|any)\b',
        code,
    ))

    # Function count estimate
    func_count = len(re.findall(
        r'(?:def |function |async function |const \w+ = (?:async )?\(|'
        r'(?:public|private|protected)\s+\w+\s*\()',
        code,
    ))
    func_count = max(func_count, 1)

    # Doc-to-function ratio
    doc_ratio = doc_blocks / func_count

    score = 0.0

    if doc_ratio > 0.8:
        score += 0.7
    elif doc_ratio > 0.4:
        score += 0.4

    # Type annotation density
    type_ratio = type_hints / total
    if type_ratio > 0.05:
        score += 0.5
    elif type_ratio > 0.02:
        score += 0.3

    return min(1.0, score / 1.2)


# ─── Public API ──────────────────────────────────────────────────────────────


def analyze_code_heuristic(code: str) -> HeuristicResult:
    """
    Analyze code using multi-signal heuristics for AI detection.

    Works on any programming language. Returns an AI probability
    between 0.0 (human) and 1.0 (AI-generated).
    """
    if not code or not code.strip():
        return HeuristicResult(ai_probability=0.5, signals={}, detection_method="heuristic")

    lines = code.split("\n")

    # Compute each signal
    signals = {
        "line_length_uniformity": _line_length_uniformity(lines),
        "comment_pattern": _comment_pattern_signal(code, lines),
        "naming_regularity": _naming_regularity_signal(code),
        "entropy_signal": _entropy_signal(code, lines),
        "structural_regularity": _structural_regularity_signal(lines),
        "boilerplate_ratio": _boilerplate_ratio_signal(code),
        "docstring_density": _docstring_density_signal(code, lines),
    }

    # Weighted combination
    ai_probability = sum(
        signals[name] * weight
        for name, weight in _SIGNAL_WEIGHTS.items()
    )

    # Clamp to [0, 1]
    ai_probability = max(0.0, min(1.0, ai_probability))

    return HeuristicResult(
        ai_probability=round(ai_probability, 4),
        signals={k: round(v, 4) for k, v in signals.items()},
        detection_method="heuristic",
    )
