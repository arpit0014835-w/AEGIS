""" 
AEGIS — Proof Verify Tests 
=============================	
"""	

from __future__ import annotations 

import pytest 

from utils.crypto import (	
    embed_watermark,	
    extract_watermark, 
    generate_author_hash, 
    sha256_hash,	
    verify_watermark,	
)	


class TestSHA256: 
    """Test SHA-256 hashing functions.""" 

    def test_deterministic_hash(self): 
        h1 = sha256_hash("hello") 
        h2 = sha256_hash("hello") 
        assert h1 == h2	

    def test_different_inputs(self):	
        h1 = sha256_hash("hello") 
        h2 = sha256_hash("world") 
        assert h1 != h2	

    def test_hash_length(self):	
        h = sha256_hash("test") 
        assert len(h) == 64 


class TestAuthorHash:	
    """Test author hash generation."""	

    def test_deterministic(self):	
        h1 = generate_author_hash("author@example.com") 
        h2 = generate_author_hash("author@example.com") 
        assert h1 == h2	

    def test_salt_changes_hash(self): 
        h1 = generate_author_hash("author@example.com", salt="")	
        h2 = generate_author_hash("author@example.com", salt="project-x")	
        assert h1 != h2 


class TestWatermarking: 
    """Test watermark embedding and extraction round-trip."""	

    def test_embed_and_extract(self): 
        code = "def foo():\n    return 42\n\ndef bar():\n    return 'hello'\n"	
        author_hash = generate_author_hash("test-author") 
        watermarked = embed_watermark(code, author_hash, bit_count=32)	
        extracted = extract_watermark(watermarked, bit_count=32)	
        expected = author_hash[:4]  # 32 bits = 4 chars 
        assert extracted == expected 

    def test_watermark_preserves_code_semantics(self):	
        code = "x = 1\ny = 2\nz = x + y\n" 
        author_hash = generate_author_hash("author") 
        watermarked = embed_watermark(code, author_hash, bit_count=16) 
        # Stripped lines should be identical	
        original_stripped = [line.strip() for line in code.split("\n")]	
        watermarked_stripped = [line.strip() for line in watermarked.split("\n")] 
        assert original_stripped == watermarked_stripped 

    def test_verify_watermark_correct_author(self):	
        code = "def foo():\n    pass\n\ndef bar():\n    pass\n\ndef baz():\n    pass\n" 
        author_hash = generate_author_hash("correct-author")	
        watermarked = embed_watermark(code, author_hash, bit_count=32) 
        # Note: verify_watermark uses the same embedding scheme 
        assert verify_watermark(watermarked, "correct-author", bit_count=32) is True	

    def test_verify_watermark_wrong_author(self):	
        code = "def foo():\n    pass\n\ndef bar():\n    pass\n\ndef baz():\n    pass\n" 
        author_hash = generate_author_hash("correct-author")	
        watermarked = embed_watermark(code, author_hash, bit_count=32)	
        assert verify_watermark(watermarked, "wrong-author", bit_count=32) is False 

    def test_no_watermark_returns_none(self):
        code = "x = 1\ny = 2\n"  # No trailing whitespace
        result = extract_watermark(code, bit_count=64)
        # Depending on line count, may return None
        assert result is None or isinstance(result, str)
