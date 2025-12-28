"""Main experiment runner script."""

import json
import random
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from context_controller import ContextController
from validate_local import validate_secrets, validate_functions_exist


class ExperimentRunner:
    """Runs the context consumption experiment."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.tests_dir = project_root / "tests"
        self.results_dir = project_root / "results"
        self.prompts_dir = project_root / "prompts"

        self.controller = ContextController(project_root)

        # Experiment configuration
        self.context_levels = {
            "30%": {"min": 25, "max": 35},
            "50%": {"min": 45, "max": 55},
            "80%": {"min": 75, "max": 85},
        }
        self.trials_per_level = 100

        # Load implementation prompt
        self.implementation_prompt = self._load_implementation_prompt()

    def _load_implementation_prompt(self) -> str:
        """Load the implementation prompt."""
        prompt_path = self.prompts_dir / "implementation_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text()
        else:
            raise FileNotFoundError(f"Implementation prompt not found at {prompt_path}")

    def setup(self) -> None:
        """Setup experiment environment."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.src_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_implementation(self) -> None:
        """Remove existing implementation file."""
        impl_file = self.src_dir / "fizzbuzz.py"
        if impl_file.exists():
            impl_file.unlink()
            print(f"Removed {impl_file}")

    def run_pytest(self) -> dict:
        """
        Run pytest and return results.

        Returns:
            Dictionary with test results
        """
        test_file = self.tests_dir / "test_fizzbuzz.py"
        if not test_file.exists():
            return {
                "exit_code": -1,
                "passed": False,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_errors": 0,
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

            # Parse pytest output
            output = result.stdout + result.stderr
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")
            errors = output.count(" ERROR")

            return {
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
                "tests_passed": passed,
                "tests_failed": failed,
                "tests_errors": errors,
                "tests_total": passed + failed + errors,
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "passed": False,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_errors": 0,
                "tests_total": 0,
                "error": "timeout",
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "passed": False,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_errors": 0,
                "tests_total": 0,
                "error": str(e),
            }

    def run_single_trial(
        self,
        trial_id: str,
        context_level: str,
        target_min: int,
        target_max: int,
    ) -> dict:
        """
        Run a single experiment trial.

        Args:
            trial_id: Unique identifier for this trial
            context_level: Target context level name (e.g., "30%")
            target_min: Minimum target context percentage
            target_max: Maximum target context percentage

        Returns:
            Dictionary with trial results
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        start_time = time.time()

        # Step 1: Clean up previous implementation
        self.cleanup_implementation()

        # Step 2: Start fresh session (reset token tracking)
        self.controller.start_trial()

        # Step 3: Inject noise to reach target context level
        context_start = 0.0
        chunk_id = 0
        max_chunks = 100

        print(f"  Adjusting context to {target_min}-{target_max}%...")
        while context_start < target_min and chunk_id < max_chunks:
            try:
                result = self.controller.inject_noise_chunk(chunk_id)
                if not result.success:
                    print(f"  Warning: Chunk {chunk_id} injection failed: {result.error}")
                context_start = self.controller.get_context_percent()
                chunk_id += 1

                if context_start > target_max:
                    print(f"  Overshoot: {context_start:.1f}% > {target_max}%")
                    break

            except FileNotFoundError:
                print(f"  No more chunks available after {chunk_id}")
                break

        print(f"  Context at {context_start:.1f}% after {chunk_id} chunks")

        # Step 4: Send implementation prompt
        print("  Sending implementation prompt...")
        impl_start_time = time.time()
        impl_result = self.controller.send_implementation_prompt(self.implementation_prompt)
        implementation_time = time.time() - impl_start_time

        # Step 5: Record final context
        context_end = self.controller.get_context_percent()

        # Step 6: End session and get usage
        usage = self.controller.end_trial()

        elapsed_seconds = time.time() - start_time

        # Step 7: Run validation
        print("  Running pytest...")
        test_results = self.run_pytest()

        impl_file = self.src_dir / "fizzbuzz.py"
        secret_validation = validate_secrets(impl_file)
        func_existence = validate_functions_exist(impl_file)

        # Compile results
        result = {
            "trial_id": trial_id,
            "context_level": context_level,
            "context_actual_start": round(context_start, 2),
            "context_actual_end": round(context_end, 2),
            "chunks_injected": chunk_id,
            "timestamp": timestamp,
            "elapsed_seconds": round(elapsed_seconds, 2),
            "implementation_seconds": round(implementation_time, 2),
            # Token usage
            "total_input_tokens": usage["input_tokens"],
            "total_output_tokens": usage["output_tokens"],
            "total_tokens": usage["total_tokens"],
            # Implementation result
            "implementation_success": impl_result.success,
            "implementation_error": impl_result.error,
            "implementation_duration_ms": impl_result.duration_ms,
            # Test results
            "test_passed": test_results["passed"],
            "tests_total": test_results["tests_total"],
            "tests_passed": test_results["tests_passed"],
            "tests_failed": test_results.get("tests_failed", 0),
            # Secret validation
            "secret_header": secret_validation["has_header"],
            "secret_footer": secret_validation["has_footer"],
            "secret_refs": secret_validation["ref_count"],
            "secret_score": secret_validation["secret_score"],
            # Function existence
            "func_results": func_existence,
        }

        # Save individual trial result
        trial_file = self.results_dir / f"trial_{trial_id}.json"
        with open(trial_file, "w") as f:
            json.dump(result, f, indent=2)

        return result

    def generate_trial_order(self) -> list[tuple[str, str]]:
        """
        Generate randomized trial order.

        Returns:
            List of (trial_id, context_level) tuples
        """
        trials = []

        for level_name in self.context_levels.keys():
            for i in range(self.trials_per_level):
                trial_id = f"{level_name}_{i+1:03d}"
                trials.append((trial_id, level_name))

        # Randomize order
        random.shuffle(trials)

        return trials

    def run_experiment(self, resume_from: Optional[int] = None) -> None:
        """
        Run the full experiment.

        Args:
            resume_from: Trial index to resume from (0-indexed)
        """
        self.setup()

        trials = self.generate_trial_order()
        total_trials = len(trials)

        # Save trial order for reproducibility
        order_file = self.results_dir / "trial_order.json"
        with open(order_file, "w") as f:
            json.dump(trials, f, indent=2)

        start_idx = resume_from if resume_from else 0
        all_results = []

        # Load existing results if resuming
        results_file = self.results_dir / "results.json"
        if resume_from and results_file.exists():
            with open(results_file, "r") as f:
                all_results = json.load(f)

        print(f"Starting experiment with {total_trials} trials")
        print(f"Results will be saved to {self.results_dir}")
        print()

        for idx, (trial_id, context_level) in enumerate(trials[start_idx:], start=start_idx):
            level_config = self.context_levels[context_level]

            print(f"[{idx+1}/{total_trials}] Running trial {trial_id} ({context_level})")

            try:
                result = self.run_single_trial(
                    trial_id=trial_id,
                    context_level=context_level,
                    target_min=level_config["min"],
                    target_max=level_config["max"],
                )

                all_results.append(result)

                # Save cumulative results
                with open(results_file, "w") as f:
                    json.dump(all_results, f, indent=2)

                status = "PASS" if result["test_passed"] else "FAIL"
                print(f"  Result: {status}, Secret Score: {result['secret_score']:.2f}")
                print(f"  Tokens: {result['total_tokens']:,}")
                print()

            except Exception as e:
                print(f"  ERROR: {e}")
                # Record failed trial
                all_results.append(
                    {
                        "trial_id": trial_id,
                        "context_level": context_level,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    }
                )
                with open(results_file, "w") as f:
                    json.dump(all_results, f, indent=2)
                print()

        print("Experiment complete!")
        print(f"Results saved to {results_file}")


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

    response = input("Start experiment? (y/N): ").strip().lower()
    if response == "y":
        runner.run_experiment()
    else:
        print("Experiment cancelled.")


if __name__ == "__main__":
    main()
