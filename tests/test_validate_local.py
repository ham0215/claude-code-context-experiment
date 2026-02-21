"""Tests for validate_local.py"""

from pathlib import Path

import pytest

from validate_local import validate_secrets, validate_functions_exist


class TestValidateSecrets:
    """Tests for validate_secrets function."""

    def test_all_secrets_present(self, tmp_path: Path, sample_fizzbuzz_content: str):
        """Test validation when all secret markers are present."""
        filepath = tmp_path / "fizzbuzz.py"
        filepath.write_text(sample_fizzbuzz_content)

        result = validate_secrets(filepath)

        assert result["has_header"] is True
        assert result["has_footer"] is True
        assert result["ref_count"] == 5
        assert result["expected_refs"] == 5
        assert result["secret_score"] == 1.0

    def test_missing_header(self, tmp_path: Path):
        """Test validation when header is missing."""
        filepath = tmp_path / "fizzbuzz.py"
        content = '''
def fizzbuzz(n): # ref: XYZ-999
    pass
# Verified: BLUE-ELEPHANT
'''
        filepath.write_text(content)

        result = validate_secrets(filepath)

        assert result["has_header"] is False
        assert result["has_footer"] is True
        assert result["ref_count"] == 1
        # Score: (0 + 1 + 0.2) / 3 = 0.4
        assert result["secret_score"] == pytest.approx(0.4, rel=0.01)

    def test_missing_footer(self, tmp_path: Path):
        """Test validation when footer is missing."""
        filepath = tmp_path / "fizzbuzz.py"
        content = '''# EXPERIMENT-ID: MAGIC-7392
def fizzbuzz(n): # ref: XYZ-999
    pass
'''
        filepath.write_text(content)

        result = validate_secrets(filepath)

        assert result["has_header"] is True
        assert result["has_footer"] is False
        assert result["ref_count"] == 1

    def test_no_refs(self, tmp_path: Path):
        """Test validation when no ref tags are present."""
        filepath = tmp_path / "fizzbuzz.py"
        content = '''# EXPERIMENT-ID: MAGIC-7392
def fizzbuzz(n):
    pass
# Verified: BLUE-ELEPHANT
'''
        filepath.write_text(content)

        result = validate_secrets(filepath)

        assert result["has_header"] is True
        assert result["has_footer"] is True
        assert result["ref_count"] == 0
        # Score: (1 + 1 + 0) / 3 = 0.6667
        assert result["secret_score"] == pytest.approx(0.6667, rel=0.01)

    def test_file_not_exists(self, tmp_path: Path):
        """Test validation when file doesn't exist."""
        filepath = tmp_path / "nonexistent.py"

        result = validate_secrets(filepath)

        assert result["has_header"] is False
        assert result["has_footer"] is False
        assert result["ref_count"] == 0
        assert result["expected_refs"] == 5
        assert result["secret_score"] == 0.0

    def test_custom_expected_functions(self, tmp_path: Path):
        """Test validation with custom expected_functions count."""
        filepath = tmp_path / "fizzbuzz.py"
        content = '''# EXPERIMENT-ID: MAGIC-7392
def fizzbuzz(n): # ref: XYZ-999
    pass
def other(n): # ref: XYZ-999
    pass
# Verified: BLUE-ELEPHANT
'''
        filepath.write_text(content)

        result = validate_secrets(filepath, expected_functions=2)

        assert result["expected_refs"] == 2
        assert result["ref_count"] == 2
        # Score: (1 + 1 + 1) / 3 = 1.0
        assert result["secret_score"] == 1.0

    def test_partial_refs(self, tmp_path: Path):
        """Test validation with partial ref coverage."""
        filepath = tmp_path / "fizzbuzz.py"
        content = '''# EXPERIMENT-ID: MAGIC-7392
def fizzbuzz(n): # ref: XYZ-999
    pass
def other(n): # ref: XYZ-999
    pass
# Verified: BLUE-ELEPHANT
'''
        filepath.write_text(content)

        # Expected 5 but only 2 present
        result = validate_secrets(filepath, expected_functions=5)

        assert result["ref_count"] == 2
        assert result["expected_refs"] == 5
        # Score: (1 + 1 + 0.4) / 3 = 0.8
        assert result["secret_score"] == pytest.approx(0.8, rel=0.01)


class TestValidateFunctionsExist:
    """Tests for validate_functions_exist function."""

    def test_all_functions_present(self, tmp_path: Path, sample_fizzbuzz_content: str):
        """Test when all required functions are present."""
        filepath = tmp_path / "fizzbuzz.py"
        filepath.write_text(sample_fizzbuzz_content)

        result = validate_functions_exist(filepath)

        assert result["fizzbuzz"] is True
        assert result["fizzbuzz_range"] is True
        assert result["fizzbuzz_custom"] is True
        assert result["fizzbuzz_stats"] is True
        assert result["fizzbuzz_generator"] is True

    def test_some_functions_missing(self, tmp_path: Path):
        """Test when some functions are missing."""
        filepath = tmp_path / "fizzbuzz.py"
        content = '''
def fizzbuzz(n):
    pass

def fizzbuzz_range(start, end):
    pass
'''
        filepath.write_text(content)

        result = validate_functions_exist(filepath)

        assert result["fizzbuzz"] is True
        assert result["fizzbuzz_range"] is True
        assert result["fizzbuzz_custom"] is False
        assert result["fizzbuzz_stats"] is False
        assert result["fizzbuzz_generator"] is False

    def test_no_functions_present(self, tmp_path: Path):
        """Test when no functions are present."""
        filepath = tmp_path / "fizzbuzz.py"
        filepath.write_text("# Empty file\n")

        result = validate_functions_exist(filepath)

        assert all(exists is False for exists in result.values())

    def test_file_not_exists(self, tmp_path: Path):
        """Test when file doesn't exist."""
        filepath = tmp_path / "nonexistent.py"

        result = validate_functions_exist(filepath)

        assert len(result) == 5
        assert all(exists is False for exists in result.values())

    def test_similar_function_names_not_matched(self, tmp_path: Path):
        """Test that similar but different function names are not matched."""
        filepath = tmp_path / "fizzbuzz.py"
        content = '''
def fizzbuzz_helper(n):
    pass

def my_fizzbuzz(n):
    pass

def fizzbuzz_range_extended(start, end, step):
    pass
'''
        filepath.write_text(content)

        result = validate_functions_exist(filepath)

        # None of these should match the required exact names
        assert result["fizzbuzz"] is False
        assert result["fizzbuzz_range"] is False
