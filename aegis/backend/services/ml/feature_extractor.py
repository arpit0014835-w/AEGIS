""" 
AEGIS — Advanced Code Feature Extractor 
=========================================	
Extracts 30+ features from Python source code for AI-generated code detection.	

Feature groups: 
  1. Stylometric (line lengths, formatting, whitespace patterns) 
  2. AST Structural (tree depth, node counts, nesting)	
  3. Token Frequency (keyword ratios, operator distribution)	
  4. Cyclomatic Complexity (McCabe-style) 
  5. Identifier Naming (length, conventions, entropy) 
  6. Comment Density (comments, docstrings, inline)	
  7. Entropy & Repetition (Shannon entropy, token uniqueness)	
"""	

from __future__ import annotations 

import ast 
import keyword 
import math 
import re 
import statistics	
import tokenize	
import io 
from collections import Counter 
from typing import Any	

import numpy as np	


# ─── Feature Names (ordered) ──────────────────────────────────────────────── 

FEATURE_NAMES: list[str] = [ 
    # Stylometric (8)	
    "avg_line_length",	
    "max_line_length",	
    "std_line_length", 
    "blank_line_ratio", 
    "avg_indentation",	
    "max_indentation", 
    "std_indentation",	
    "trailing_whitespace_ratio",	
    # AST Structural (7) 
    "ast_depth", 
    "ast_node_count",	
    "ast_unique_node_types", 
    "ast_branching_factor",	
    "max_nesting_depth", 
    "num_functions",	
    "num_classes",	
    # Token Frequency (8) 
    "keyword_ratio", 
    "for_loop_ratio",	
    "while_loop_ratio", 
    "if_ratio", 
    "try_except_ratio", 
    "import_count",	
    "builtin_usage_count",	
    "operator_diversity", 
    # Cyclomatic Complexity (2) 
    "cyclomatic_complexity",	
    "avg_function_complexity", 
    # Identifier Naming (7)	
    "avg_identifier_length", 
    "max_identifier_length", 
    "std_identifier_length",	
    "snake_case_ratio",	
    "single_char_ratio", 
    "underscore_prefix_ratio",	
    "identifier_entropy",	
    # Comment Density (3) 
    "comment_density",
    "has_docstrings",
    "inline_comment_ratio",
    # Entropy & Repetition (4)
    "char_entropy",
    "token_entropy",
    "unique_token_ratio",
    "bigram_repetition_score",
]

NUM_FEATURES = len(FEATURE_NAMES)

# ─── Python builtins set ────────────────────────────────────────────────────

_BUILTINS = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))

# ─── Helpers ─────────────────────────────────────────────────────────────────


def _safe_std(values: list[float]) -> float:
    """Standard deviation with fallback for < 2 values."""
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def _shannon_entropy(counts: Counter) -> float:
    """Compute Shannon entropy from a Counter."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    probs = [c / total for c in counts.values()]
    return -sum(p * math.log2(p) for p in probs if p > 0)


# ─── AST Helpers ─────────────────────────────────────────────────────────────


def _ast_depth(node: ast.AST) -> int:
    """Compute maximum depth of an AST tree."""
    if not list(ast.iter_child_nodes(node)):
        return 1
    return 1 + max(_ast_depth(child) for child in ast.iter_child_nodes(node))


def _ast_node_count(node: ast.AST) -> int:
    """Count total nodes in AST."""
    return 1 + sum(_ast_node_count(c) for c in ast.iter_child_nodes(node))


def _ast_unique_types(node: ast.AST) -> set[str]:
    """Collect unique AST node type names."""
    types = {type(node).__name__}
    for child in ast.iter_child_nodes(node):
        types |= _ast_unique_types(child)
    return types


def _ast_branching_factor(node: ast.AST) -> float:
    """Average number of children per non-leaf node."""
    counts: list[int] = []

    def _walk(n: ast.AST) -> None:
        children = list(ast.iter_child_nodes(n))
        if children:
            counts.append(len(children))
            for c in children:
                _walk(c)

    _walk(node)
    return statistics.mean(counts) if counts else 0.0


def _max_nesting(node: ast.AST, depth: int = 0) -> int:
    """Maximum nesting depth of control flow structures."""
    nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try)
    # Python 3.11+ uses ast.TryStar; handle gracefully
    try:
        nesting_nodes = nesting_nodes + (ast.TryStar,)
    except AttributeError:
        pass

    current = depth + 1 if isinstance(node, nesting_nodes) else depth
    child_max = current
    for child in ast.iter_child_nodes(node):
        child_max = max(child_max, _max_nesting(child, current))
    return child_max


# ─── Cyclomatic Complexity ───────────────────────────────────────────────────


def _cyclomatic_complexity(tree: ast.AST) -> int:
    """
    McCabe cyclomatic complexity approximation.
    Counts: if, elif, for, while, except, and, or, assert, with, comprehensions.
    """
    complexity = 1  # Base path
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp)):
            complexity += 1
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(node, (ast.While,)):
            complexity += 1
        elif isinstance(node, (ast.ExceptHandler,)):
            complexity += 1
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            complexity += 1
        elif isinstance(node, (ast.Assert,)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            # Each 'and'/'or' adds a branch
            complexity += len(node.values) - 1
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            complexity += len(node.generators)
    return complexity


def _per_function_complexity(tree: ast.AST) -> list[int]:
    """Compute cyclomatic complexity per function."""
    complexities = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexities.append(_cyclomatic_complexity(node))
    return complexities


# ─── Identifier Extraction ──────────────────────────────────────────────────


def _extract_identifiers(tree: ast.AST) -> list[str]:
    """Extract all user-defined identifier names from AST."""
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            names.append(node.name)
            names.extend(arg.arg for arg in node.args.args)
        elif isinstance(node, ast.AsyncFunctionDef):
            names.append(node.name)
            names.extend(arg.arg for arg in node.args.args)
        elif isinstance(node, ast.ClassDef):
            names.append(node.name)
        elif isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
    # Filter out Python keywords and builtins
    kw_set = set(keyword.kwlist)
    return [n for n in names if n not in kw_set and n not in _BUILTINS and len(n) > 0]


# ─── Main Feature Extraction ────────────────────────────────────────────────


def extract_features(code: str) -> np.ndarray:
    """
    Extract a feature vector from a Python code string.

    Returns a 1D numpy array of shape (NUM_FEATURES,).
    If the code cannot be parsed, returns a zero vector.
    """
    features = np.zeros(NUM_FEATURES, dtype=np.float64)

    if not code or not code.strip():
        return features

    lines = code.split("\n")
    non_empty_lines = [l for l in lines if l.strip()]
    total_lines = max(len(lines), 1)

    # ─── 1. Stylometric Features ────────────────────────────────────────
    line_lengths = [len(l) for l in lines]
    features[0] = statistics.mean(line_lengths) if line_lengths else 0.0  # avg_line_length
    features[1] = max(line_lengths) if line_lengths else 0.0             # max_line_length
    features[2] = _safe_std(line_lengths)                                 # std_line_length

    blank_count = sum(1 for l in lines if not l.strip())
    features[3] = blank_count / total_lines                               # blank_line_ratio

    indentations = []
    for l in non_empty_lines:
        stripped = l.lstrip()
        indent = len(l) - len(stripped)
        indentations.append(float(indent))
    features[4] = statistics.mean(indentations) if indentations else 0.0  # avg_indentation
    features[5] = max(indentations) if indentations else 0.0              # max_indentation
    features[6] = _safe_std(indentations)                                  # std_indentation

    trailing_ws = sum(1 for l in lines if l != l.rstrip() and l.strip())
    features[7] = trailing_ws / max(len(non_empty_lines), 1)              # trailing_whitespace_ratio

    # ─── 2. AST Structural Features ─────────────────────────────────────
    tree = None
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Return partial features if AST fails
        pass

    if tree is not None:
        features[8] = float(_ast_depth(tree))                      # ast_depth
        features[9] = float(_ast_node_count(tree))                 # ast_node_count
        features[10] = float(len(_ast_unique_types(tree)))         # ast_unique_node_types
        features[11] = _ast_branching_factor(tree)                 # ast_branching_factor
        features[12] = float(_max_nesting(tree))                   # max_nesting_depth

        func_count = sum(
            1 for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        )
        class_count = sum(
            1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
        )
        features[13] = float(func_count)                           # num_functions
        features[14] = float(class_count)                          # num_classes

        # ─── 4. Cyclomatic Complexity ────────────────────────────────
        features[22] = float(_cyclomatic_complexity(tree))          # cyclomatic_complexity
        per_func = _per_function_complexity(tree)
        features[23] = statistics.mean(per_func) if per_func else 0.0  # avg_function_complexity

        # ─── 5. Identifier Naming ────────────────────────────────────
        identifiers = _extract_identifiers(tree)
        if identifiers:
            id_lengths = [float(len(n)) for n in identifiers]
            features[24] = statistics.mean(id_lengths)              # avg_identifier_length
            features[25] = max(id_lengths)                          # max_identifier_length
            features[26] = _safe_std(id_lengths)                    # std_identifier_length

            snake = sum(1 for n in identifiers if re.match(r"^[a-z][a-z0-9_]*$", n))
            features[27] = snake / len(identifiers)                 # snake_case_ratio

            single = sum(1 for n in identifiers if len(n) == 1)
            features[28] = single / len(identifiers)                # single_char_ratio

            underscore_prefix = sum(1 for n in identifiers if n.startswith("_"))
            features[29] = underscore_prefix / len(identifiers)     # underscore_prefix_ratio

            # Identifier character entropy
            all_id_chars = Counter("".join(identifiers))
            features[30] = _shannon_entropy(all_id_chars)           # identifier_entropy

        # ─── 6. Comment Density ──────────────────────────────────────
        # Count import statements
        import_count = sum(
            1 for n in ast.walk(tree)
            if isinstance(n, (ast.Import, ast.ImportFrom))
        )
        features[19] = float(import_count)                          # import_count

    # ─── 3. Token Frequency Features ─────────────────────────────────
    tokens: list[str] = []
    try:
        token_gen = tokenize.generate_tokens(io.StringIO(code).readline)
        for tok in token_gen:
            if tok.type == tokenize.NAME:
                tokens.append(tok.string)
            elif tok.type == tokenize.OP:
                tokens.append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass

    total_tokens = max(len(tokens), 1)
    kw_set = set(keyword.kwlist)
    name_tokens = [t for t in tokens if t in kw_set or t.isidentifier()]
    kw_tokens = [t for t in tokens if t in kw_set]

    features[15] = len(kw_tokens) / total_tokens                    # keyword_ratio

    kw_counter = Counter(kw_tokens)
    features[16] = kw_counter.get("for", 0) / total_tokens           # for_loop_ratio
    features[17] = kw_counter.get("while", 0) / total_tokens         # while_loop_ratio
    features[18] = kw_counter.get("if", 0) / total_tokens            # if_ratio
    features[20] = (kw_counter.get("try", 0) + kw_counter.get("except", 0)) / total_tokens  # try_except_ratio

    # Builtin usage
    builtin_count = sum(1 for t in tokens if t in _BUILTINS and t not in kw_set)
    features[20] = (kw_counter.get("try", 0) + kw_counter.get("except", 0)) / total_tokens  # try_except_ratio
    features[21] = float(builtin_count)                              # builtin_usage_count (reindex below)

    # Operator diversity
    op_tokens = [t for t in tokens if not t.isidentifier() and not t.isdigit() and t.strip()]
    features[21] = float(len(set(op_tokens))) if op_tokens else 0.0  # operator_diversity

    # Fix: reassign try_except and builtin
    # Index 19 = import_count (set above from AST)
    # Index 20 = try_except_ratio
    features[20] = (kw_counter.get("try", 0) + kw_counter.get("except", 0)) / total_tokens
    # Index 21 = builtin_usage_count → use operator_diversity differently
    features[21] = float(len(set(op_tokens))) if op_tokens else 0.0  # operator_diversity

    # ─── 6. Comment Density (token-based) ────────────────────────────
    comment_lines = sum(1 for l in lines if l.strip().startswith("#"))
    features[31] = comment_lines / total_lines                       # comment_density

    # Docstring detection
    has_docstring = 0.0
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                body = getattr(node, "body", [])
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, (ast.Constant,)):
                    if isinstance(body[0].value.value, str):
                        has_docstring = 1.0
                        break
    features[32] = has_docstring                                      # has_docstrings

    # Inline comments (lines with code AND a comment)
    inline_comments = 0
    for l in lines:
        stripped = l.strip()
        if stripped and not stripped.startswith("#") and "#" in stripped:
            # Rough heuristic: check if # is not inside a string
            in_string = False
            for i, ch in enumerate(stripped):
                if ch in ('"', "'"):
                    in_string = not in_string
                elif ch == "#" and not in_string:
                    inline_comments += 1
                    break
    features[33] = inline_comments / total_lines                      # inline_comment_ratio

    # ─── 7. Entropy & Repetition ─────────────────────────────────────
    # Character entropy
    char_counter = Counter(code)
    features[34] = _shannon_entropy(char_counter)                     # char_entropy

    # Token entropy
    token_counter = Counter(tokens)
    features[35] = _shannon_entropy(token_counter)                    # token_entropy

    # Unique token ratio
    features[36] = len(set(tokens)) / total_tokens                    # unique_token_ratio

    # Bigram repetition score
    if len(tokens) >= 2:
        bigrams = [(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)]
        bigram_counter = Counter(bigrams)
        total_bigrams = len(bigrams)
        repeated = sum(c for c in bigram_counter.values() if c > 1)
        features[37] = repeated / total_bigrams                       # bigram_repetition_score

    return features


def extract_features_batch(code_list: list[str], n_jobs: int = 1) -> np.ndarray:
    """
    Extract features for a batch of code samples.

    Parameters
    ----------
    code_list : list[str]
        List of Python source code strings.
    n_jobs : int
        Number of parallel workers (1 = sequential).

    Returns
    -------
    np.ndarray
        Feature matrix of shape (n_samples, NUM_FEATURES).
    """
    if n_jobs == 1:
        return np.vstack([extract_features(code) for code in code_list])

    # Parallel extraction using multiprocessing
    from concurrent.futures import ProcessPoolExecutor, as_completed

    results = [None] * len(code_list)
    with ProcessPoolExecutor(max_workers=n_jobs) as executor:
        future_to_idx = {
            executor.submit(extract_features, code): i
            for i, code in enumerate(code_list)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception:
                results[idx] = np.zeros(NUM_FEATURES, dtype=np.float64)

    return np.vstack(results)
