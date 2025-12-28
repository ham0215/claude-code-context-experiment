"""Tests for experiment_runner.py"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from experiment_runner import ExperimentRunner
from claude_sdk_wrapper import SessionResult


class TestExperimentRunner:
    """Tests for ExperimentRunner class."""

    @pytest.fixture
    def runner_with_prompt(self, project_root: Path) -> ExperimentRunner:
        """Create runner with implementation prompt."""
        prompt_path = project_root / "prompts" / "implementation_prompt.txt"
        prompt_path.write_text("Implement FizzBuzz")

        with patch("experiment_runner.ContextController"):
            runner = ExperimentRunner(project_root)
            return runner

    def test_init(self, project_root: Path):
        """Test runner initialization."""
        prompt_path = project_root / "prompts" / "implementation_prompt.txt"
        prompt_path.write_text("Test prompt")

        with patch("experiment_runner.ContextController"):
            runner = ExperimentRunner(project_root)

            assert runner.project_root == project_root
            assert runner.src_dir == project_root / "src"
            assert runner.tests_dir == project_root / "tests"
            assert runner.results_dir == project_root / "results"
            assert runner.trials_per_level == 100
            assert len(runner.context_levels) == 3
            assert "30%" in runner.context_levels
            assert "50%" in runner.context_levels
            assert "80%" in runner.context_levels

    def test_init_prompt_not_found(self, project_root: Path):
        """Test initialization when prompt file is missing."""
        with patch("experiment_runner.ContextController"):
            with pytest.raises(FileNotFoundError) as exc_info:
                ExperimentRunner(project_root)

            assert "implementation_prompt.txt" in str(exc_info.value)

    def test_setup(self, runner_with_prompt: ExperimentRunner, project_root: Path):
        """Test experiment setup creates directories."""
        runner_with_prompt.setup()

        assert (project_root / "results").exists()
        assert (project_root / "src").exists()

    def test_cleanup_implementation(self, runner_with_prompt: ExperimentRunner, project_root: Path):
        """Test cleaning up implementation file."""
        impl_file = project_root / "src" / "fizzbuzz.py"
        impl_file.write_text("# Test content")

        runner_with_prompt.cleanup_implementation()

        assert not impl_file.exists()

    def test_cleanup_implementation_no_file(self, runner_with_prompt: ExperimentRunner):
        """Test cleanup when file doesn't exist (no error)."""
        runner_with_prompt.cleanup_implementation()
        # Should not raise

    def test_run_pytest_success(self, runner_with_prompt: ExperimentRunner, project_root: Path):
        """Test running pytest successfully."""
        test_file = project_root / "tests" / "test_fizzbuzz.py"
        test_file.write_text("# Test file")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="test_1 PASSED\ntest_2 PASSED\ntest_3 PASSED",
                stderr=""
            )

            result = runner_with_prompt.run_pytest()

            assert result["passed"] is True
            assert result["exit_code"] == 0
            assert result["tests_passed"] == 3

    def test_run_pytest_failure(self, runner_with_prompt: ExperimentRunner, project_root: Path):
        """Test running pytest with failures."""
        test_file = project_root / "tests" / "test_fizzbuzz.py"
        test_file.write_text("# Test file")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="test_1 PASSED\ntest_2 FAILED\ntest_3 ERROR",
                stderr=""
            )

            result = runner_with_prompt.run_pytest()

            assert result["passed"] is False
            assert result["exit_code"] == 1
            assert result["tests_passed"] == 1
            assert result["tests_failed"] == 1
            assert result["tests_errors"] == 1

    def test_run_pytest_test_file_not_found(self, runner_with_prompt: ExperimentRunner):
        """Test running pytest when test file doesn't exist."""
        result = runner_with_prompt.run_pytest()

        assert result["passed"] is False
        assert result["exit_code"] == -1
        assert "error" in result

    def test_run_pytest_timeout(self, runner_with_prompt: ExperimentRunner, project_root: Path):
        """Test pytest timeout handling."""
        test_file = project_root / "tests" / "test_fizzbuzz.py"
        test_file.write_text("# Test file")

        import subprocess
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=60)

            result = runner_with_prompt.run_pytest()

            assert result["passed"] is False
            assert result["error"] == "timeout"

    def test_generate_trial_order(self, runner_with_prompt: ExperimentRunner):
        """Test trial order generation."""
        runner_with_prompt.trials_per_level = 3  # Reduce for testing

        trials = runner_with_prompt.generate_trial_order()

        # Should have 3 levels * 3 trials = 9 trials
        assert len(trials) == 9

        # Check that all levels are represented
        levels = [t[1] for t in trials]
        assert levels.count("30%") == 3
        assert levels.count("50%") == 3
        assert levels.count("80%") == 3

        # Trial IDs should be unique
        trial_ids = [t[0] for t in trials]
        assert len(trial_ids) == len(set(trial_ids))

    def test_generate_trial_order_randomized(self, runner_with_prompt: ExperimentRunner):
        """Test that trial order is randomized."""
        runner_with_prompt.trials_per_level = 10

        # Generate multiple orders and check they're not all the same
        orders = [tuple(runner_with_prompt.generate_trial_order()) for _ in range(5)]

        # Very unlikely all 5 will be identical if randomization works
        assert len(set(orders)) > 1


class TestRunSingleTrial:
    """Tests for run_single_trial method."""

    @pytest.fixture
    def runner_with_mocks(self, project_root: Path):
        """Create runner with mocked dependencies."""
        prompt_path = project_root / "prompts" / "implementation_prompt.txt"
        prompt_path.write_text("Implement FizzBuzz")

        mock_result = SessionResult(
            success=True,
            input_tokens=5000,
            output_tokens=2000,
            total_tokens=7000,
            content="Implementation complete",
            session_id="test-session",
            duration_ms=5000,
        )

        with patch("experiment_runner.ContextController") as mock_controller_cls:
            mock_controller = MagicMock()
            mock_controller.get_context_percent.return_value = 30.0
            mock_controller.inject_noise_chunk.return_value = mock_result
            mock_controller.send_implementation_prompt.return_value = mock_result
            mock_controller.start_trial.return_value = None
            mock_controller.end_trial.return_value = {
                "input_tokens": 50000,
                "output_tokens": 5000,
                "total_tokens": 55000,
            }
            mock_controller_cls.return_value = mock_controller

            runner = ExperimentRunner(project_root)
            runner.controller = mock_controller
            yield runner

    def test_run_single_trial_success(
        self, runner_with_mocks: ExperimentRunner, project_root: Path, sample_fizzbuzz_content: str
    ):
        """Test running a successful trial."""
        # Create fizzbuzz.py after "implementation"
        impl_file = project_root / "src" / "fizzbuzz.py"

        def create_impl(*args, **kwargs):
            impl_file.write_text(sample_fizzbuzz_content)
            return runner_with_mocks.controller.send_implementation_prompt.return_value

        runner_with_mocks.controller.send_implementation_prompt.side_effect = create_impl

        # Mock pytest
        test_file = project_root / "tests" / "test_fizzbuzz.py"
        test_file.write_text("# Test")

        with patch.object(runner_with_mocks, "run_pytest") as mock_pytest:
            mock_pytest.return_value = {
                "passed": True,
                "exit_code": 0,
                "tests_passed": 5,
                "tests_failed": 0,
                "tests_errors": 0,
                "tests_total": 5,
            }

            result = runner_with_mocks.run_single_trial(
                trial_id="30%_001",
                context_level="30%",
                target_min=25,
                target_max=35,
            )

            assert result["trial_id"] == "30%_001"
            assert result["context_level"] == "30%"
            assert result["test_passed"] is True
            assert result["secret_score"] == 1.0
            assert "timestamp" in result
            assert "elapsed_seconds" in result

    def test_run_single_trial_test_failed(
        self, runner_with_mocks: ExperimentRunner, project_root: Path
    ):
        """Test trial when tests fail."""
        impl_file = project_root / "src" / "fizzbuzz.py"

        def create_impl(*args, **kwargs):
            impl_file.write_text("def fizzbuzz(n): pass")  # Incomplete impl
            return runner_with_mocks.controller.send_implementation_prompt.return_value

        runner_with_mocks.controller.send_implementation_prompt.side_effect = create_impl

        test_file = project_root / "tests" / "test_fizzbuzz.py"
        test_file.write_text("# Test")

        with patch.object(runner_with_mocks, "run_pytest") as mock_pytest:
            mock_pytest.return_value = {
                "passed": False,
                "exit_code": 1,
                "tests_passed": 1,
                "tests_failed": 4,
                "tests_errors": 0,
                "tests_total": 5,
            }

            result = runner_with_mocks.run_single_trial(
                trial_id="80%_001",
                context_level="80%",
                target_min=75,
                target_max=85,
            )

            assert result["test_passed"] is False
            assert result["tests_failed"] == 4

    def test_run_single_trial_saves_to_file(
        self, runner_with_mocks: ExperimentRunner, project_root: Path, sample_fizzbuzz_content: str
    ):
        """Test that trial results are saved to individual file."""
        impl_file = project_root / "src" / "fizzbuzz.py"

        def create_impl(*args, **kwargs):
            impl_file.write_text(sample_fizzbuzz_content)
            return runner_with_mocks.controller.send_implementation_prompt.return_value

        runner_with_mocks.controller.send_implementation_prompt.side_effect = create_impl

        test_file = project_root / "tests" / "test_fizzbuzz.py"
        test_file.write_text("# Test")

        with patch.object(runner_with_mocks, "run_pytest") as mock_pytest:
            mock_pytest.return_value = {
                "passed": True,
                "exit_code": 0,
                "tests_passed": 5,
                "tests_failed": 0,
                "tests_errors": 0,
                "tests_total": 5,
            }

            runner_with_mocks.setup()
            result = runner_with_mocks.run_single_trial(
                trial_id="30%_001",
                context_level="30%",
                target_min=25,
                target_max=35,
            )

            trial_file = project_root / "results" / "trial_30%_001.json"
            assert trial_file.exists()

            with open(trial_file) as f:
                saved_result = json.load(f)
            assert saved_result["trial_id"] == "30%_001"


class TestContextLevels:
    """Tests for context level configuration."""

    def test_context_level_ranges(self, project_root: Path):
        """Test context level min/max ranges."""
        prompt_path = project_root / "prompts" / "implementation_prompt.txt"
        prompt_path.write_text("Test")

        with patch("experiment_runner.ContextController"):
            runner = ExperimentRunner(project_root)

            assert runner.context_levels["30%"]["min"] == 25
            assert runner.context_levels["30%"]["max"] == 35
            assert runner.context_levels["50%"]["min"] == 45
            assert runner.context_levels["50%"]["max"] == 55
            assert runner.context_levels["80%"]["min"] == 75
            assert runner.context_levels["80%"]["max"] == 85
