"""Tests for calibration.py"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from calibration import Calibrator
from claude_sdk_wrapper import SessionResult


class TestCalibrator:
    """Tests for Calibrator class."""

    def test_init(self, project_root: Path):
        """Test calibrator initialization."""
        with patch("calibration.ContextController"):
            calibrator = Calibrator(project_root)

            assert calibrator.project_root == project_root
            assert calibrator.results_file == project_root / "results" / "calibration.json"

    def test_calibrate_success(self, project_root: Path):
        """Test successful calibration."""
        # Create noise chunks
        for i in range(6):
            chunk_path = project_root / "noise_chunks" / f"chunk_{i}.txt"
            chunk_path.write_text(f"Noise chunk {i}")

        mock_result = SessionResult(
            success=True,
            input_tokens=5000,
            output_tokens=100,
            total_tokens=5100,
            content="Acknowledged",
            session_id="test-session",
            duration_ms=1000,
        )

        context_values = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0]
        context_iter = iter(context_values)

        with patch("calibration.ContextController") as mock_controller_cls:
            mock_controller = MagicMock()
            mock_controller.get_context_percent.side_effect = lambda: next(context_iter)
            mock_controller.inject_noise_chunk.return_value = mock_result
            mock_controller.start_trial.return_value = None
            mock_controller.end_trial.return_value = {
                "input_tokens": 30000,
                "output_tokens": 600,
                "total_tokens": 30600,
                "context_percent": 15.0,
            }
            mock_controller_cls.return_value = mock_controller

            calibrator = Calibrator(project_root)
            result = calibrator.calibrate(num_samples=6)

            assert "error" not in result
            assert result["num_samples"] == 6
            assert result["successful_samples"] == 6
            assert "average_increase_percent" in result
            assert "average_input_tokens_per_chunk" in result
            assert "measurements" in result
            assert len(result["measurements"]) == 6

    def test_calibrate_partial_success(self, project_root: Path):
        """Test calibration with some failures."""
        # Create only 3 noise chunks
        for i in range(3):
            chunk_path = project_root / "noise_chunks" / f"chunk_{i}.txt"
            chunk_path.write_text(f"Noise chunk {i}")

        mock_result_success = SessionResult(
            success=True,
            input_tokens=5000,
            output_tokens=100,
            total_tokens=5100,
            content="Acknowledged",
            session_id="test-session",
            duration_ms=1000,
        )

        mock_result_fail = SessionResult(
            success=False,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            content="",
            error="Rate limit exceeded",
            duration_ms=0,
        )

        context_values = [0.0, 2.5, 5.0, 7.5]
        context_iter = iter(context_values)

        with patch("calibration.ContextController") as mock_controller_cls:
            mock_controller = MagicMock()
            mock_controller.get_context_percent.side_effect = lambda: next(context_iter)
            # First two succeed, third fails
            mock_controller.inject_noise_chunk.side_effect = [
                mock_result_success,
                mock_result_success,
                mock_result_fail,
                FileNotFoundError("No more chunks"),
            ]
            mock_controller.start_trial.return_value = None
            mock_controller.end_trial.return_value = {
                "input_tokens": 10000,
                "output_tokens": 200,
                "total_tokens": 10200,
                "context_percent": 5.0,
            }
            mock_controller_cls.return_value = mock_controller

            calibrator = Calibrator(project_root)
            result = calibrator.calibrate(num_samples=6)

            assert result["num_samples"] == 3
            assert result["successful_samples"] == 2

    def test_calibrate_no_chunks(self, project_root: Path):
        """Test calibration when no chunks are available."""
        with patch("calibration.ContextController") as mock_controller_cls:
            mock_controller = MagicMock()
            mock_controller.get_context_percent.return_value = 0.0
            mock_controller.inject_noise_chunk.side_effect = FileNotFoundError("No chunks")
            mock_controller.start_trial.return_value = None
            mock_controller.end_trial.return_value = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "context_percent": 0.0,
            }
            mock_controller_cls.return_value = mock_controller

            calibrator = Calibrator(project_root)
            result = calibrator.calibrate(num_samples=6)

            assert "error" in result
            assert result["error"] == "No measurements collected"

    def test_calibrate_stops_at_context_limit(self, project_root: Path):
        """Test calibration stops when context limit approaches."""
        # Create noise chunks
        for i in range(10):
            chunk_path = project_root / "noise_chunks" / f"chunk_{i}.txt"
            chunk_path.write_text(f"Noise chunk {i}")

        mock_result = SessionResult(
            success=True,
            input_tokens=50000,
            output_tokens=100,
            total_tokens=50100,
            content="Acknowledged",
            session_id="test-session",
            duration_ms=1000,
        )

        # Each chunk increases by 25%, so after 4 chunks we hit 85+
        context_values = [0.0, 25.0, 50.0, 75.0, 90.0]
        context_iter = iter(context_values)

        with patch("calibration.ContextController") as mock_controller_cls:
            mock_controller = MagicMock()
            mock_controller.get_context_percent.side_effect = lambda: next(context_iter)
            mock_controller.inject_noise_chunk.return_value = mock_result
            mock_controller.start_trial.return_value = None
            mock_controller.end_trial.return_value = {
                "input_tokens": 200000,
                "output_tokens": 400,
                "total_tokens": 200400,
                "context_percent": 90.0,
            }
            mock_controller_cls.return_value = mock_controller

            calibrator = Calibrator(project_root)
            result = calibrator.calibrate(num_samples=10)

            # Should stop before completing all 10 samples
            assert result["num_samples"] < 10

    def test_save_results(self, project_root: Path):
        """Test saving calibration results."""
        with patch("calibration.ContextController"):
            calibrator = Calibrator(project_root)

            test_data = {
                "timestamp": "2024-01-01T00:00:00Z",
                "average_increase_percent": 2.5,
                "num_samples": 6,
            }

            calibrator.save_results(test_data)

            assert calibrator.results_file.exists()
            with open(calibrator.results_file) as f:
                saved_data = json.load(f)
            assert saved_data == test_data

    def test_load_results_exists(self, project_root: Path):
        """Test loading existing calibration results."""
        test_data = {
            "timestamp": "2024-01-01T00:00:00Z",
            "average_increase_percent": 2.5,
            "num_samples": 6,
        }

        results_file = project_root / "results" / "calibration.json"
        with open(results_file, "w") as f:
            json.dump(test_data, f)

        with patch("calibration.ContextController"):
            calibrator = Calibrator(project_root)
            loaded = calibrator.load_results()

            assert loaded == test_data

    def test_load_results_not_exists(self, project_root: Path):
        """Test loading when no results file exists."""
        with patch("calibration.ContextController"):
            calibrator = Calibrator(project_root)
            loaded = calibrator.load_results()

            assert loaded is None


class TestCalibrationMeasurements:
    """Test measurement calculations in calibration."""

    def test_measurement_data_structure(self, project_root: Path):
        """Test that measurements have correct structure."""
        chunk_path = project_root / "noise_chunks" / "chunk_0.txt"
        chunk_path.write_text("Noise")

        mock_result = SessionResult(
            success=True,
            input_tokens=5000,
            output_tokens=100,
            total_tokens=5100,
            content="Acknowledged",
            session_id="test-session",
            duration_ms=1234,
        )

        context_values = [0.0, 2.55]
        context_iter = iter(context_values)

        with patch("calibration.ContextController") as mock_controller_cls:
            mock_controller = MagicMock()
            mock_controller.get_context_percent.side_effect = lambda: next(context_iter)
            mock_controller.inject_noise_chunk.side_effect = [
                mock_result,
                FileNotFoundError("No more"),
            ]
            mock_controller.start_trial.return_value = None
            mock_controller.end_trial.return_value = {
                "input_tokens": 5000,
                "output_tokens": 100,
                "total_tokens": 5100,
                "context_percent": 2.55,
            }
            mock_controller_cls.return_value = mock_controller

            calibrator = Calibrator(project_root)
            result = calibrator.calibrate(num_samples=3)

            assert len(result["measurements"]) == 1
            m = result["measurements"][0]
            assert m["chunk_id"] == 0
            assert m["before_percent"] == 0.0
            assert m["after_percent"] == 2.55
            assert m["increase_percent"] == 2.55
            assert m["input_tokens"] == 5000
            assert m["output_tokens"] == 100
            assert m["total_tokens"] == 5100
            assert m["success"] is True
            assert m["duration_ms"] == 1234
