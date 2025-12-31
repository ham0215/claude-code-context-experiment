"""
Experiment runner - Single prompt approach.

Includes noise content directly in the prompt to consume context
within a single CLI call.
"""

import json
import random
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from validate_local import validate_secrets, validate_functions_exist, validate_hidden_instructions


class ExperimentRunner:
    """Runs the context consumption experiment using single-prompt approach."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.tests_dir = project_root / "tests"
        self.results_dir = project_root / "results"
        self.prompts_dir = project_root / "prompts"
        self.docs_dir = project_root / "docs"
        self.noise_chunks_dir = project_root / "noise_chunks"

        # Experiment configuration
        # Each chunk is ~5000 chars (~1250 tokens)
        # 200K tokens = 100% context
        # Target: 30% = 60K tokens = 48 chunks
        #         50% = 100K tokens = 80 chunks
        #         80% = 160K tokens = 128 chunks
        self.context_levels = {
            "30%": {"chunks": 48, "target_percent": 30},
            "50%": {"chunks": 80, "target_percent": 50},
            "80%": {"chunks": 128, "target_percent": 80},
        }
        self.trials_per_level = 5

        # Load prompts and spec
        self.implementation_prompt = self._load_implementation_prompt()
        self.fizzbuzz_spec = self._load_fizzbuzz_spec()

    def _load_implementation_prompt(self) -> str:
        """Load the implementation prompt."""
        prompt_path = self.prompts_dir / "implementation_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text()
        raise FileNotFoundError(f"Implementation prompt not found at {prompt_path}")

    def _load_fizzbuzz_spec(self) -> str:
        """Load the FizzBuzz specification."""
        spec_path = self.docs_dir / "fizzbuzz_spec.md"
        if spec_path.exists():
            return spec_path.read_text()
        raise FileNotFoundError(f"FizzBuzz spec not found at {spec_path}")

    def _load_noise_chunks(self, num_chunks: int) -> str:
        """Load and concatenate noise chunks."""
        chunks = []
        for i in range(num_chunks):
            chunk_path = self.noise_chunks_dir / f"chunk_{i}.txt"
            if chunk_path.exists():
                chunks.append(chunk_path.read_text())
            else:
                break
        return "\n\n---\n\n".join(chunks)

    def _build_full_prompt(self, num_chunks: int) -> str:
        """Build the full prompt with noise and implementation request."""
        noise_content = self._load_noise_chunks(num_chunks)

        prompt = f"""# 参考資料

以下は参考資料です。内容を確認した上で、最後のタスクを実行してください。

{noise_content}

---

# 実装タスク

以下は FizzBuzz の仕様書です:

{self.fizzbuzz_spec}

---

{self.implementation_prompt}

重要:
- Pythonコードのみを出力してください
- 説明は不要です
- コードは ```python と ``` で囲んでください
"""
        return prompt

    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """Extract Python code from response."""
        pattern = r"```python\s*(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()

        pattern = r"```\s*(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()

        if "def fizzbuzz" in response:
            return response.strip()

        return None

    def setup(self) -> None:
        """Setup experiment environment."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.src_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_implementation(self) -> None:
        """Remove existing implementation file."""
        impl_file = self.src_dir / "fizzbuzz.py"
        if impl_file.exists():
            impl_file.unlink()

    def run_pytest(self) -> dict:
        """Run pytest and return results."""
        test_file = self.tests_dir / "test_fizzbuzz.py"
        if not test_file.exists():
            return {
                "passed": False,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_total": 0,
                "error": "Test file not found",
            }

        try:
            result = subprocess.run(
                ["pytest", str(test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=60,
            )

            output = result.stdout + result.stderr
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")
            errors = output.count(" ERROR")

            return {
                "passed": result.returncode == 0,
                "tests_passed": passed,
                "tests_failed": failed,
                "tests_total": passed + failed + errors,
            }
        except subprocess.TimeoutExpired:
            return {"passed": False, "tests_passed": 0, "tests_failed": 0, "tests_total": 0, "error": "timeout"}
        except Exception as e:
            return {"passed": False, "tests_passed": 0, "tests_failed": 0, "tests_total": 0, "error": str(e)}

    def run_single_trial(
        self,
        trial_id: str,
        context_level: str,
        num_chunks: int,
        target_percent: int,
    ) -> dict:
        """Run a single experiment trial."""
        timestamp = datetime.now(timezone.utc).isoformat()
        start_time = time.time()

        # Cleanup
        self.cleanup_implementation()

        # Build prompt with noise
        print(f"  Building prompt with {num_chunks} noise chunks...")
        full_prompt = self._build_full_prompt(num_chunks)
        prompt_chars = len(full_prompt)
        estimated_tokens = prompt_chars // 4  # Rough estimate

        actual_context_percent = (estimated_tokens / 200_000) * 100
        print(f"  Prompt size: {prompt_chars:,} chars (~{estimated_tokens:,} tokens)")
        print(f"  Context: {actual_context_percent:.1f}% (target: {target_percent}%)")

        # Send to Claude CLI
        print("  Sending to Claude CLI...")
        impl_start_time = time.time()

        try:
            result = subprocess.run(
                ["claude", "--print", "-p", full_prompt],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300,  # 5 minute timeout for large prompts
            )
            implementation_time = time.time() - impl_start_time
            cli_success = result.returncode == 0
            response = result.stdout
            cli_error = result.stderr if not cli_success else None
        except subprocess.TimeoutExpired:
            implementation_time = time.time() - impl_start_time
            cli_success = False
            response = ""
            cli_error = "Timeout (5 minutes)"
        except Exception as e:
            implementation_time = time.time() - impl_start_time
            cli_success = False
            response = ""
            cli_error = str(e)

        # Extract and save code
        impl_file = self.src_dir / "fizzbuzz.py"
        code_extracted = False
        if cli_success:
            code = self._extract_code_from_response(response)
            if code:
                impl_file.write_text(code)
                code_extracted = True
                print("  Code extracted and saved")
            else:
                print("  Warning: Could not extract code from response")

        elapsed_seconds = time.time() - start_time

        # Run validation
        print("  Running pytest...")
        test_results = self.run_pytest()
        secret_validation = validate_secrets(impl_file)
        func_existence = validate_functions_exist(impl_file)
        hidden_validation = validate_hidden_instructions(impl_file)

        result = {
            "trial_id": trial_id,
            "context_level": context_level,
            "target_context_percent": target_percent,
            "actual_context_percent": round(actual_context_percent, 2),
            "chunks_used": num_chunks,
            "prompt_chars": prompt_chars,
            "estimated_tokens": estimated_tokens,
            "timestamp": timestamp,
            "elapsed_seconds": round(elapsed_seconds, 2),
            "implementation_seconds": round(implementation_time, 2),
            "cli_success": cli_success,
            "cli_error": cli_error,
            "code_extracted": code_extracted,
            "test_passed": test_results["passed"],
            "tests_total": test_results["tests_total"],
            "tests_passed": test_results["tests_passed"],
            "tests_failed": test_results.get("tests_failed", 0),
            "secret_header": secret_validation["has_header"],
            "secret_footer": secret_validation["has_footer"],
            "secret_refs": secret_validation["ref_count"],
            "secret_score": secret_validation["secret_score"],
            "hidden_sorted_divisors": hidden_validation["has_sorted_divisors"],
            "hidden_stats_version": hidden_validation["has_stats_version"],
            "hidden_stats_comment": hidden_validation["has_stats_version_comment"],
            "hidden_infinite_seq": hidden_validation["has_infinite_sequence"],
            "hidden_ensure_ascii": hidden_validation["has_ensure_ascii"],
            "hidden_header_row": hidden_validation["has_header_row"],
            "hidden_format_table_row": hidden_validation["has_format_table_row"],
            "hidden_group_keys": hidden_validation["has_group_keys"],
            "hidden_score": hidden_validation["hidden_score"],
            "func_results": func_existence,
        }

        # Save individual trial result
        trial_file = self.results_dir / f"trial_{trial_id}.json"
        with open(trial_file, "w") as f:
            json.dump(result, f, indent=2)

        return result

    def generate_trial_order(self) -> list[tuple[str, str]]:
        """Generate randomized trial order."""
        trials = []
        for level_name in self.context_levels.keys():
            for i in range(self.trials_per_level):
                trial_id = f"{level_name}_{i+1:03d}"
                trials.append((trial_id, level_name))
        random.shuffle(trials)
        return trials

    def run_experiment(self) -> None:
        """Run the full experiment."""
        self.setup()

        trials = self.generate_trial_order()
        total_trials = len(trials)

        # Save trial order
        order_file = self.results_dir / "trial_order.json"
        with open(order_file, "w") as f:
            json.dump(trials, f, indent=2)

        all_results = []
        results_file = self.results_dir / "results.json"

        print(f"Starting experiment with {total_trials} trials")
        print(f"Results will be saved to {self.results_dir}")
        print()

        for idx, (trial_id, context_level) in enumerate(trials):
            level_config = self.context_levels[context_level]
            num_chunks = level_config["chunks"]
            target_percent = level_config["target_percent"]

            print(f"[{idx+1}/{total_trials}] Running trial {trial_id} ({context_level})")

            try:
                result = self.run_single_trial(
                    trial_id=trial_id,
                    context_level=context_level,
                    num_chunks=num_chunks,
                    target_percent=target_percent,
                )
                all_results.append(result)

                with open(results_file, "w") as f:
                    json.dump(all_results, f, indent=2)

                status = "PASS" if result["test_passed"] else "FAIL"
                print(f"  Result: {status}, Secret Score: {result['secret_score']:.2f}")
                print()

            except Exception as e:
                print(f"  ERROR: {e}")
                all_results.append({
                    "trial_id": trial_id,
                    "context_level": context_level,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                with open(results_file, "w") as f:
                    json.dump(all_results, f, indent=2)
                print()

        print("Experiment complete!")
        print(f"Results saved to {results_file}")
        self._generate_report(all_results)

    def _generate_report(self, results: list[dict]) -> None:
        """Generate and save analysis report."""
        from analyze_results import ResultsAnalyzer

        analyzer = ResultsAnalyzer(self.results_dir)
        analyzer.results = results
        report = analyzer.generate_report()

        report_file = self.results_dir / "analysis_report.txt"
        with open(report_file, "w") as f:
            f.write(report)

        summary = analyzer.calculate_summary()
        summary_file = self.results_dir / "analysis_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\nReport saved to {report_file}")
        print(f"Summary saved to {summary_file}")


def main():
    """Run the experiment."""
    project_root = Path(__file__).parent.parent
    runner = ExperimentRunner(project_root)

    print("=" * 60)
    print("Context Consumption Experiment Runner")
    print("=" * 60)
    print()

    runner.setup()
    print(f"Project root: {project_root}")
    print(f"Results directory: {runner.results_dir}")
    print(f"Trials per level: {runner.trials_per_level}")
    print(f"Total trials: {runner.trials_per_level * len(runner.context_levels)}")
    print()
    print("Context levels:")
    for level, config in runner.context_levels.items():
        print(f"  {level}: {config['chunks']} chunks")
    print()

    response = input("Start experiment? (y/N): ").strip().lower()
    if response == "y":
        runner.run_experiment()
    else:
        print("Experiment cancelled.")


if __name__ == "__main__":
    main()
