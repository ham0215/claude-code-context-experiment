"""Validation logic for experiment results."""

import re
from pathlib import Path
from typing import TypedDict


class SecretValidation(TypedDict):
    has_header: bool
    has_footer: bool
    ref_count: int
    expected_refs: int
    secret_score: float


class HiddenInstructionValidation(TypedDict):
    # Original 5 functions
    has_sorted_divisors: bool       # _sorted_divisors in fizzbuzz_custom
    has_stats_version: bool         # STATS_VERSION = "1.0" constant
    has_stats_version_comment: bool # # Uses STATS_VERSION in fizzbuzz_stats
    has_infinite_sequence: bool     # "infinite sequence" in generator docstring
    # New formatter functions
    has_ensure_ascii: bool          # ensure_ascii=False in fizzbuzz_json
    has_header_row: bool            # _header_row variable in fizzbuzz_csv
    has_format_table_row: bool      # _format_table_row helper in fizzbuzz_markdown_table
    has_group_keys: bool            # GROUP_KEYS constant for fizzbuzz_grouped
    hidden_score: float


def validate_secrets(filepath: Path, expected_functions: int = 9) -> SecretValidation:
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
        "fizzbuzz_generator",
        "fizzbuzz_json",
        "fizzbuzz_csv",
        "fizzbuzz_markdown_table",
        "fizzbuzz_grouped",
    ]

    if not filepath.exists():
        return {func: False for func in required_functions}

    content = filepath.read_text()

    return {
        func: f"def {func}(" in content
        for func in required_functions
    }


def validate_hidden_instructions(filepath: Path) -> HiddenInstructionValidation:
    """
    Validate hidden instructions embedded in the middle of the specification.

    These instructions test whether Claude reads the entire spec carefully:
    Original functions:
    1. _sorted_divisors variable name in fizzbuzz_custom
    2. STATS_VERSION = "1.0" constant at module level
    3. "# Uses STATS_VERSION" comment in fizzbuzz_stats
    4. "infinite sequence" phrase in fizzbuzz_generator docstring

    New formatter functions:
    5. ensure_ascii=False in fizzbuzz_json
    6. _header_row variable in fizzbuzz_csv
    7. _format_table_row helper function in fizzbuzz_markdown_table
    8. GROUP_KEYS constant for fizzbuzz_grouped

    Args:
        filepath: Path to the fizzbuzz.py implementation file

    Returns:
        Dictionary with validation results and hidden instruction score
    """
    if not filepath.exists():
        return {
            "has_sorted_divisors": False,
            "has_stats_version": False,
            "has_stats_version_comment": False,
            "has_infinite_sequence": False,
            "has_ensure_ascii": False,
            "has_header_row": False,
            "has_format_table_row": False,
            "has_group_keys": False,
            "hidden_score": 0.0
        }

    content = filepath.read_text()

    # Check 1: _sorted_divisors in fizzbuzz_custom
    has_sorted_divisors = "_sorted_divisors" in content

    # Check 2: STATS_VERSION = "1.0" constant
    has_stats_version = bool(re.search(r'STATS_VERSION\s*=\s*["\']1\.0["\']', content))

    # Check 3: # Uses STATS_VERSION comment in fizzbuzz_stats function
    has_stats_version_comment = "Uses STATS_VERSION" in content

    # Check 4: "infinite sequence" in fizzbuzz_generator docstring
    generator_match = re.search(
        r'def fizzbuzz_generator\([^)]*\)[^:]*:[\s\n]*("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')',
        content
    )
    has_infinite_sequence = False
    if generator_match:
        docstring = generator_match.group(1)
        has_infinite_sequence = "infinite sequence" in docstring.lower()

    # Check 5: ensure_ascii=False in fizzbuzz_json
    has_ensure_ascii = "ensure_ascii=False" in content or "ensure_ascii = False" in content

    # Check 6: _header_row variable in fizzbuzz_csv
    has_header_row = "_header_row" in content

    # Check 7: _format_table_row helper function in fizzbuzz_markdown_table
    has_format_table_row = "def _format_table_row(" in content

    # Check 8: GROUP_KEYS constant for fizzbuzz_grouped
    has_group_keys = bool(re.search(r'GROUP_KEYS\s*=', content))

    # Calculate score (each check is worth 12.5%)
    checks = [
        has_sorted_divisors,
        has_stats_version,
        has_stats_version_comment,
        has_infinite_sequence,
        has_ensure_ascii,
        has_header_row,
        has_format_table_row,
        has_group_keys,
    ]
    hidden_score = sum(1 for c in checks if c) / len(checks)

    return {
        "has_sorted_divisors": has_sorted_divisors,
        "has_stats_version": has_stats_version,
        "has_stats_version_comment": has_stats_version_comment,
        "has_infinite_sequence": has_infinite_sequence,
        "has_ensure_ascii": has_ensure_ascii,
        "has_header_row": has_header_row,
        "has_format_table_row": has_format_table_row,
        "has_group_keys": has_group_keys,
        "hidden_score": round(hidden_score, 4)
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

    print("\nHidden Instructions:")
    hidden = validate_hidden_instructions(test_path)
    for key, value in hidden.items():
        status = "✓" if value else "✗" if isinstance(value, bool) else f"{value:.1%}"
        print(f"  {status} {key}")
