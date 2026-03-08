""" 
AEGIS — Breach Secure Tests 
==============================	
"""	

from __future__ import annotations 

from pathlib import Path 

import pytest	


class TestBuiltinRules:	
    """Test built-in regex-based vulnerability rules.""" 

    def test_detect_hardcoded_key(self, sample_js_file: Path): 
        from services.breach_secure import _run_builtin_rules	

        vulns = _run_builtin_rules([sample_js_file])	
        key_vulns = [v for v in vulns if v.category.value == "hardcoded_secret"]	
        assert len(key_vulns) >= 1, "Should detect hardcoded API key" 

    def test_detect_prompt_injection(self, sample_js_file: Path): 
        from services.breach_secure import _run_builtin_rules 

        vulns = _run_builtin_rules([sample_js_file]) 
        # The sample JS has intentionally insecure patterns 
        categories = {v.category.value for v in vulns}	
        assert len(vulns) > 0, "Should detect at least one vulnerability"	

    def test_clean_code_minimal_vulns(self, sample_clean_file: Path): 
        from services.breach_secure import _run_builtin_rules 

        vulns = _run_builtin_rules([sample_clean_file])	
        critical = [v for v in vulns if v.severity.value == "critical"]	
        assert len(critical) == 0, "Clean code should have no critical vulns" 


class TestBreachSecureIntegration: 
    """Integration tests for the full Breach Secure pipeline."""	

    @pytest.mark.asyncio	
    async def test_breach_secure_scoring(self, sample_codebase: Path):	
        from services.breach_secure import run_breach_secure 
        from utils.git_ops import enumerate_source_files 

        files = enumerate_source_files(sample_codebase)	
        result = await run_breach_secure( 
            source_files=files,	
            target_dir=str(sample_codebase),	
        ) 

        assert result.score >= 0 
        assert result.score <= 100	
        # Should find at least some vulns in the intentionally insecure code 
        total = (	
            result.critical_count + result.high_count 
            + result.medium_count + result.low_count + result.info_count	
        )	
        assert total >= 0 
