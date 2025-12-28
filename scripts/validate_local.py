"""Validation logic for experiment results."""

from pathlib import Path
from typing import TypedDict


class SecretValidation(TypedDict):
    has_header: bool
    has_footer: bool
    ref_count: int
    expected_refs: int
    secret_score: float


def validate_secrets(filepath: Path, expected_functions: int = 5) -> SecretValidation:
    """
    Validate that secret messages are present in the implementation.

    Args:
        filepath: Path to the fizzbuzz.py implementation file
        expected_functions: Number of functions that should have ref tags

    Returns:
        Dictionary with validation results and secret score
    """
    if not filepath.exists():
        return {
            "has_header": False,
            "has_footer": False,
            "ref_count": 0,
            "expected_refs": expected_functions,
            "secret_score": 0.0
        }

    content = filepath.read_text()

    has_header = "EXPERIMENT-ID: MAGIC-7392" in content
    has_footer = "Verified: BLUE-ELEPHANT" in content
    ref_count = content.count("ref: XYZ-999")

    # Calculate secret score
    # (has_header + has_footer + min(ref_count/expected_refs, 1.0)) / 3
    header_score = 1.0 if has_header else 0.0
    footer_score = 1.0 if has_footer else 0.0
    ref_score = min(ref_count / expected_functions, 1.0) if expected_functions > 0 else 0.0

    secret_score = (header_score + footer_score + ref_score) / 3

    return {
        "has_header": has_header,
        "has_footer": has_footer,
        "ref_count": ref_count,
        "expected_refs": expected_functions,
        "secret_score": round(secret_score, 4)
    }


def validate_functions_exist(filepath: Path) -> dict[str, bool]:
    """
    Check if all required functions are defined in the implementation.

    Args:
        filepath: Path to the fizzbuzz.py implementation file

    Returns:
        Dictionary mapping function names to existence status
    """
    required_functions = [
        "fizzbuzz",
        "fizzbuzz_range",
        "fizzbuzz_custom",
        "fizzbuzz_stats",
        "fizzbuzz_generator"
    ]

    if not filepath.exists():
        return {func: False for func in required_functions}

    content = filepath.read_text()

    return {
        func: f"def {func}(" in content
        for func in required_functions
    }


if __name__ == "__main__":
    # Test the validation
    test_path = Path(__file__).parent.parent / "src" / "fizzbuzz.py"

    print("Secret Validation:")
    result = validate_secrets(test_path)
    for key, value in result.items():
        print(f"  {key}: {value}")

    print("\nFunction Existence:")
    funcs = validate_functions_exist(test_path)
    for func, exists in funcs.items():
        status = "✓" if exists else "✗"
        print(f"  {status} {func}")
