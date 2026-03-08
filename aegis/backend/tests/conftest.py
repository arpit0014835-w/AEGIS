""" 
AEGIS — Test Configuration & Fixtures 
========================================	
Shared fixtures for the test suite.	
""" 

from __future__ import annotations 

import tempfile	
from pathlib import Path	

import pytest 


# ─── Sample Code Fixtures ─────────────────────────────────────────────────── 

SAMPLE_PYTHON_CODE = '''"""Sample module for testing."""	

import os	
import json	
from pathlib import Path 
from typing import Optional 

import requests 
import fake_nonexistent_package 


def fetch_data(url: str, timeout: int = 30) -> Optional[dict]: 
    """Fetch JSON data from a URL."""	
    response = requests.get(url, timeout=timeout)	
    response.raise_for_status() 
    return response.json() 


def process_items(items: list[dict]) -> list[str]:	
    """Process a list of items and return names."""	
    results = [] 
    for item in items: 
        name = item.get("name", "")	
        if name:	
            results.append(name.strip().lower())	
    return results 


class DataProcessor: 
    """Processes structured data."""	

    def __init__(self, config: dict): 
        self.config = config	
        self._cache = {}	

    def transform(self, data: dict) -> dict: 
        """Apply transformations to data.""" 
        return {k: str(v).upper() for k, v in data.items()}	
''' 

# NOTE: Sample intentionally-insecure JS code for testing.	
# Strings are split to prevent AEGIS self-scan false positives. 
_JS_API_KEY_VAL = "sk-1234567890" + "abcdefghijklmnop"	

SAMPLE_JS_CODE = (	
    "import React from 'react';\n" 
    "import { useState } from 'react';\n" 
    "import nonExistentLib from 'fake-js-package';\n"	
    "\n" 
    "const API_KEY" + " = \"" + _JS_API_KEY_VAL + "\";\n" 
    "\n" 
    "function fetchUserData(userId) {\n"	
    "    const response = fetch(`/api/users/${userId}`);\n"	
    "    return response.json();\n" 
    "}\n" 
    "\n"	
    "const processResults = async (query) => {\n" 
    "    const prompt_text = `Analyse this: ${query}`;\n"	
    "    const res = await " 
    "openai" 
    ".complete(prompt_text);\n"	
    "    return ev" + "al(res" + ".text);\n"	
    "};\n" 
    "\n"	
    "export default function App() {\n"	
    "    const [data, setData] = useState(null);\n" 
    "    return <div>{data}</div>;\n"
    "}\n"
)

SAMPLE_CLEAN_CODE = '''"""Clean, consistent code for testing."""

import os
import sys


def calculate_sum(numbers: list[int]) -> int:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def calculate_average(numbers: list[int]) -> float:
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
'''


@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    """Create a temporary Python file with sample code."""
    f = tmp_path / "sample.py"
    f.write_text(SAMPLE_PYTHON_CODE, encoding="utf-8")
    return f


@pytest.fixture
def sample_js_file(tmp_path: Path) -> Path:
    """Create a temporary JavaScript file with sample code."""
    f = tmp_path / "sample.js"
    f.write_text(SAMPLE_JS_CODE, encoding="utf-8")
    return f


@pytest.fixture
def sample_clean_file(tmp_path: Path) -> Path:
    """Create a clean Python file for comparison."""
    f = tmp_path / "clean.py"
    f.write_text(SAMPLE_CLEAN_CODE, encoding="utf-8")
    return f


@pytest.fixture
def sample_codebase(tmp_path: Path) -> Path:
    """Create a temporary codebase with multiple files."""
    (tmp_path / "main.py").write_text(SAMPLE_PYTHON_CODE, encoding="utf-8")
    (tmp_path / "utils.py").write_text(SAMPLE_CLEAN_CODE, encoding="utf-8")
    (tmp_path / "app.js").write_text(SAMPLE_JS_CODE, encoding="utf-8")
    return tmp_path
