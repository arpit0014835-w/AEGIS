""" 
AEGIS — Feature Extractor Tests 
=================================	
Unit tests for each feature group extracted by the ML pipeline.	
""" 

from __future__ import annotations 

import numpy as np	
import pytest	

from services.ml.feature_extractor import ( 
    FEATURE_NAMES, 
    NUM_FEATURES,	
    extract_features,	
    extract_features_batch,	
) 


# ─── Test Samples ──────────────────────────────────────────────────────────── 

SIMPLE_PYTHON = ''' 
def hello(): 
    """Say hello.""" 
    print("Hello, world!")	

def add(a, b):	
    return a + b 
''' 

COMPLEX_PYTHON = '''	
import os	
import sys 
from collections import defaultdict 

# Global config	
MAX_RETRIES = 3	

class DataProcessor:	
    """Process data from various sources.""" 

    def __init__(self, config: dict): 
        self._config = config	
        self._cache = {} 

    def process(self, data: list[dict]) -> list[str]:	
        """Process a list of data items."""	
        results = [] 
        for item in data: 
            if item.get("valid"):	
                try: 
                    name = item["name"].strip().lower()	
                    if name and name not in self._cache: 
                        self._cache[name] = True	
                        results.append(name)	
                except (KeyError, AttributeError): 
                    continue 
        return results	

    def _validate(self, item: dict) -> bool: 
        """Check if an item is valid.""" 
        return bool(item.get("name")) and isinstance(item.get("value"), (int, float)) 
'''	

EMPTY_CODE = ""	

SYNTAX_ERROR_CODE = ''' 
def broken( 
    print("no closing paren"	
''' 


# ─── Tests ───────────────────────────────────────────────────────────────────	


class TestFeatureExtraction: 
    """Test basic feature extraction.""" 

    def test_feature_vector_shape(self):	
        features = extract_features(SIMPLE_PYTHON)	
        assert features.shape == (NUM_FEATURES,) 
        assert len(FEATURE_NAMES) == NUM_FEATURES	

    def test_empty_code_returns_zeros(self):	
        features = extract_features(EMPTY_CODE) 
        assert features.shape == (NUM_FEATURES,)
        assert np.allclose(features, 0.0)

    def test_syntax_error_partial_features(self):
        features = extract_features(SYNTAX_ERROR_CODE)
        assert features.shape == (NUM_FEATURES,)
        # Stylometric features should still be extracted
        assert features[0] > 0  # avg_line_length should be non-zero

    def test_simple_vs_complex_complexity(self):
        simple_f = extract_features(SIMPLE_PYTHON)
        complex_f = extract_features(COMPLEX_PYTHON)
        # Complex code should have higher cyclomatic complexity
        # Index 22 = cyclomatic_complexity
        assert complex_f[22] > simple_f[22]

    def test_complex_has_more_functions(self):
        simple_f = extract_features(SIMPLE_PYTHON)
        complex_f = extract_features(COMPLEX_PYTHON)
        # Index 13 = num_functions
        assert simple_f[13] == 2  # hello, add
        assert complex_f[13] >= 2  # process, _validate, __init__

    def test_comment_density(self):
        features = extract_features(COMPLEX_PYTHON)
        # Index 31 = comment_density
        assert features[31] > 0  # Has comments

    def test_has_docstrings(self):
        features = extract_features(COMPLEX_PYTHON)
        # Index 32 = has_docstrings
        assert features[32] == 1.0

    def test_import_count(self):
        features = extract_features(COMPLEX_PYTHON)
        # Index 19 = import_count
        assert features[19] >= 3  # os, sys, collections

    def test_ast_depth_positive(self):
        features = extract_features(COMPLEX_PYTHON)
        # Index 8 = ast_depth
        assert features[8] > 0

    def test_identifier_naming(self):
        features = extract_features(COMPLEX_PYTHON)
        # Index 24 = avg_identifier_length
        assert features[24] > 0
        # Index 27 = snake_case_ratio
        assert features[27] >= 0

    def test_entropy_features(self):
        features = extract_features(COMPLEX_PYTHON)
        # Index 34 = char_entropy
        assert features[34] > 0
        # Index 35 = token_entropy
        assert features[35] > 0


class TestBatchExtraction:
    """Test batch feature extraction."""

    def test_batch_shape(self):
        codes = [SIMPLE_PYTHON, COMPLEX_PYTHON, EMPTY_CODE]
        result = extract_features_batch(codes)
        assert result.shape == (3, NUM_FEATURES)

    def test_batch_matches_individual(self):
        codes = [SIMPLE_PYTHON, COMPLEX_PYTHON]
        batch = extract_features_batch(codes)

        for i, code in enumerate(codes):
            individual = extract_features(code)
            np.testing.assert_array_almost_equal(batch[i], individual)


class TestFeatureNames:
    """Test feature name consistency."""

    def test_feature_count_matches(self):
        assert len(FEATURE_NAMES) == NUM_FEATURES

    def test_feature_names_unique(self):
        assert len(FEATURE_NAMES) == len(set(FEATURE_NAMES))

    def test_all_features_named(self):
        for name in FEATURE_NAMES:
            assert isinstance(name, str)
            assert len(name) > 0
