"""Pytest configuration and fixtures for scripts tests."""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary project root with required directories."""
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "results").mkdir()
    (tmp_path / "prompts").mkdir()
    (tmp_path / "noise_chunks").mkdir()
    return tmp_path


@pytest.fixture
def sample_fizzbuzz_content() -> str:
    """Sample fizzbuzz.py content with all secret markers."""
    return '''"""
EXPERIMENT-ID: MAGIC-7392
FizzBuzz Implementation
"""

def fizzbuzz(n: int) -> str:
    """Return fizzbuzz string for n. ref: XYZ-999"""
    if n % 15 == 0:
        return "FizzBuzz"
    elif n % 3 == 0:
        return "Fizz"
    elif n % 5 == 0:
        return "Buzz"
    return str(n)


def fizzbuzz_range(start: int, end: int) -> list[str]:
    """Return fizzbuzz for range. ref: XYZ-999"""
    return [fizzbuzz(i) for i in range(start, end + 1)]


def fizzbuzz_custom(n: int, divisors: dict) -> str:
    """Custom divisor fizzbuzz. ref: XYZ-999"""
    result = ""
    for divisor, word in sorted(divisors.items()):
        if n % divisor == 0:
            result += word
    return result if result else str(n)


def fizzbuzz_stats(numbers: list[int]) -> dict:
    """Get fizzbuzz stats. ref: XYZ-999"""
    results = [fizzbuzz(n) for n in numbers]
    return {
        "fizz": results.count("Fizz"),
        "buzz": results.count("Buzz"),
        "fizzbuzz": results.count("FizzBuzz"),
    }


def fizzbuzz_generator(limit: int):
    """Generate fizzbuzz values. ref: XYZ-999"""
    for i in range(1, limit + 1):
        yield fizzbuzz(i)


# Verified: BLUE-ELEPHANT
'''


@pytest.fixture
def sample_results_data() -> list[dict]:
    """Sample experiment results for testing analysis."""
    return [
        {
            "trial_id": "30%_001",
            "context_level": "30%",
            "test_passed": True,
            "secret_score": 1.0,
            "elapsed_seconds": 45.5,
            "func_results": {
                "fizzbuzz": True,
                "fizzbuzz_range": True,
                "fizzbuzz_custom": True,
                "fizzbuzz_stats": True,
                "fizzbuzz_generator": True,
            },
        },
        {
            "trial_id": "30%_002",
            "context_level": "30%",
            "test_passed": True,
            "secret_score": 0.67,
            "elapsed_seconds": 52.3,
            "func_results": {
                "fizzbuzz": True,
                "fizzbuzz_range": True,
                "fizzbuzz_custom": True,
                "fizzbuzz_stats": False,
                "fizzbuzz_generator": True,
            },
        },
        {
            "trial_id": "80%_001",
            "context_level": "80%",
            "test_passed": False,
            "secret_score": 0.33,
            "elapsed_seconds": 78.2,
            "func_results": {
                "fizzbuzz": True,
                "fizzbuzz_range": True,
                "fizzbuzz_custom": False,
                "fizzbuzz_stats": False,
                "fizzbuzz_generator": False,
            },
        },
        {
            "trial_id": "80%_002",
            "context_level": "80%",
            "test_passed": False,
            "secret_score": 0.0,
            "elapsed_seconds": 95.1,
            "func_results": {
                "fizzbuzz": True,
                "fizzbuzz_range": False,
                "fizzbuzz_custom": False,
                "fizzbuzz_stats": False,
                "fizzbuzz_generator": False,
            },
        },
    ]


@pytest.fixture
def mock_session_result():
    """Create a mock SessionResult."""
    from claude_sdk_wrapper import SessionResult

    return SessionResult(
        success=True,
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
        content="Acknowledged",
        session_id="test-session-123",
        duration_ms=1234,
    )
