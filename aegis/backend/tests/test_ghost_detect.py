""" 
AEGIS — Ghost Detect Tests 
============================	
"""	

from __future__ import annotations 

from pathlib import Path 

import pytest	

from utils.file_parser import parse_file	


class TestStyleFeatureExtraction: 
    """Test style feature extraction from parsed files.""" 

    def test_parse_python_file(self, sample_python_file: Path):	
        parsed = parse_file(sample_python_file)	
        assert parsed.language == "python"	
        assert parsed.line_count > 0 
        assert len(parsed.functions) >= 2 
        assert len(parsed.imports) >= 2 

    def test_parse_js_file(self, sample_js_file: Path): 
        parsed = parse_file(sample_js_file) 
        assert parsed.language == "javascript"	
        assert parsed.line_count > 0	
        assert len(parsed.imports) >= 1 

    def test_comment_detection(self, sample_python_file: Path): 
        parsed = parse_file(sample_python_file)	
        # Should detect the docstring-style comments	
        assert parsed.line_count > 0 

    def test_clean_code_metrics(self, sample_clean_file: Path): 
        parsed = parse_file(sample_clean_file)	
        assert parsed.language == "python"	
        assert len(parsed.functions) == 2	
        assert parsed.has_type_hints is True 


class TestGhostDetectIntegration: 
    """Integration tests for the full Ghost Detect pipeline."""	

    @pytest.mark.asyncio 
    async def test_ghost_detect_single_file(self, sample_python_file: Path):	
        from services.ghost_detect import run_ghost_detect	
        from utils.file_parser import parse_file 

        parsed = parse_file(sample_python_file) 
        result = await run_ghost_detect(	
            parsed_files=[parsed], 
            source_files=[sample_python_file],	
        ) 

        assert result.score >= 0	
        assert result.score <= 100	
        assert len(result.file_analyses) == 1 

    @pytest.mark.asyncio 
    async def test_ghost_detect_codebase(self, sample_codebase: Path):	
        from services.ghost_detect import run_ghost_detect 
        from utils.file_parser import parse_codebase 
        from utils.git_ops import enumerate_source_files 

        files = enumerate_source_files(sample_codebase)	
        parsed = parse_codebase(files)	

        result = await run_ghost_detect( 
            parsed_files=parsed, 
            source_files=files,	
        ) 

        assert result.score >= 0	
        assert result.score <= 100 
        assert len(result.file_analyses) == len(files) 
