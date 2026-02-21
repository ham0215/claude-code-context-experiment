"""Verify all trial results: run tests and validation, update result JSON files."""

import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from validate_local import (
    validate_functions_exist,
    validate_hidden_instructions,
    validate_secrets,
)


def verify_all_trials():
    result_files = sorted(glob.glob("results/trial_*.json"))
    if not result_files:
        print("No trial result files found in results/")
        return

    for result_file in result_files:
        with open(result_file) as f:
            result = json.load(f)

        workspace = result["workspace_path"]
        impl_file = Path(workspace) / "src" / "fizzbuzz.py"
        trial_id = result["trial_id"]

        print(f"\n=== Verifying {trial_id} ===")

        # 1. Run tests
        env = os.environ.copy()
        env["PYTHONPATH"] = f'{workspace}/src:{env.get("PYTHONPATH", "")}'
        proc = subprocess.run(
            ["python3", "-m", "pytest", "tests/test_fizzbuzz.py", "-v"],
            capture_output=True,
            text=True,
            env=env,
        )

        # Parse test results
        test_passed = proc.returncode == 0
        tests_passed = 0
        tests_failed = 0
        combined_output = proc.stdout + proc.stderr
        passed_match = re.search(r"(\d+) passed", combined_output)
        failed_match = re.search(r"(\d+) failed", combined_output)
        if passed_match:
            tests_passed = int(passed_match.group(1))
        if failed_match:
            tests_failed = int(failed_match.group(1))

        print(
            f'  Tests: {"PASS" if test_passed else "FAIL"}'
            f" ({tests_passed} passed, {tests_failed} failed)"
        )

        # 2. Run validation
        secrets = validate_secrets(impl_file)
        funcs = validate_functions_exist(impl_file)
        hidden = validate_hidden_instructions(impl_file)

        print(
            f'  Secret score: {secrets["secret_score"]},'
            f' Hidden score: {hidden["hidden_score"]}'
        )

        # 3. Update result JSON with test & validation fields
        result.update(
            {
                "test_passed": test_passed,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "secret_header": secrets["has_header"],
                "secret_footer": secrets["has_footer"],
                "secret_refs": secrets["ref_count"],
                "secret_score": secrets["secret_score"],
                "hidden_sorted_divisors": hidden["has_sorted_divisors"],
                "hidden_stats_version": hidden["has_stats_version"],
                "hidden_stats_comment": hidden["has_stats_version_comment"],
                "hidden_infinite_seq": hidden["has_infinite_sequence"],
                "hidden_ensure_ascii": hidden["has_ensure_ascii"],
                "hidden_header_row": hidden["has_header_row"],
                "hidden_format_table_row": hidden["has_format_table_row"],
                "hidden_group_keys": hidden["has_group_keys"],
                "hidden_score": hidden["hidden_score"],
                "func_results": funcs,
            }
        )

        with open(result_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"  Updated: {result_file}")

    print("\n=== All verifications complete ===")


if __name__ == "__main__":
    verify_all_trials()
