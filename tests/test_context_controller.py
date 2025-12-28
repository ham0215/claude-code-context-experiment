"""Tests for context_controller.py"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from context_controller import ContextController, estimate_chunks_needed
from claude_sdk_wrapper import SessionResult


class TestContextController:
    """Tests for ContextController class."""

    def test_init(self, project_root: Path):
        """Test controller initialization."""
        with patch("context_controller.ClaudeSessionManager"):
            controller = ContextController(project_root)

            assert controller.project_root == project_root
            assert controller.noise_chunks_dir == project_root / "noise_chunks"
            assert controller.prompts_dir == project_root / "prompts"
            assert controller.chunk_increase_rate is None

    def test_load_noise_template_from_file(self, project_root: Path):
        """Test loading noise template from file."""
        template_content = "Custom template: {noise_content}"
        template_path = project_root / "prompts" / "noise_prompt_template.txt"
        template_path.write_text(template_content)

        with patch("context_controller.ClaudeSessionManager"):
            controller = ContextController(project_root)
            template = controller._load_noise_template()

            assert template == template_content

    def test_load_noise_template_default(self, project_root: Path):
        """Test default noise template when file doesn't exist."""
        with patch("context_controller.ClaudeSessionManager"):
            controller = ContextController(project_root)
            template = controller._load_noise_template()

            assert "{noise_content}" in template
            assert "Acknowledged" in template

    def test_get_context_percent(self, project_root: Path):
        """Test getting context percentage."""
        with patch("context_controller.ClaudeSessionManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_manager.get_context_percent.return_value = 25.5
            mock_manager_cls.return_value = mock_manager

            controller = ContextController(project_root)
            percent = controller.get_context_percent()

            assert percent == 25.5
            mock_manager.get_context_percent.assert_called_once()

    def test_clear_context(self, project_root: Path):
        """Test clearing context."""
        with patch("context_controller.ClaudeSessionManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_manager_cls.return_value = mock_manager

            controller = ContextController(project_root)
            result = controller.clear_context()

            assert result is True
            mock_manager.reset_usage.assert_called_once()

    def test_inject_noise_chunk_success(self, project_root: Path, mock_session_result):
        """Test injecting a noise chunk."""
        # Create noise chunk file
        chunk_path = project_root / "noise_chunks" / "chunk_0.txt"
        chunk_path.write_text("This is noise content for testing.")

        with patch("context_controller.ClaudeSessionManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_manager.send_message.return_value = mock_session_result
            mock_manager_cls.return_value = mock_manager

            controller = ContextController(project_root)
            result = controller.inject_noise_chunk(0)

            assert result.success is True
            mock_manager.send_message.assert_called_once()
            # Check that prompt contains noise content
            call_args = mock_manager.send_message.call_args[0][0]
            assert "This is noise content" in call_args

    def test_inject_noise_chunk_file_not_found(self, project_root: Path):
        """Test injecting noise chunk when file doesn't exist."""
        with patch("context_controller.ClaudeSessionManager"):
            controller = ContextController(project_root)

            with pytest.raises(FileNotFoundError) as exc_info:
                controller.inject_noise_chunk(99)

            assert "chunk_99.txt" in str(exc_info.value)

    def test_send_implementation_prompt(self, project_root: Path, mock_session_result):
        """Test sending implementation prompt."""
        with patch("context_controller.ClaudeSessionManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_manager.send_message.return_value = mock_session_result
            mock_manager_cls.return_value = mock_manager

            controller = ContextController(project_root)
            result = controller.send_implementation_prompt("Implement fizzbuzz")

            assert result.success is True
            mock_manager.send_message.assert_called_once_with("Implement fizzbuzz")

    def test_start_trial(self, project_root: Path):
        """Test starting a new trial."""
        with patch("context_controller.ClaudeSessionManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_manager_cls.return_value = mock_manager

            controller = ContextController(project_root)
            controller.start_trial()

            mock_manager.reset_usage.assert_called_once()

    def test_end_trial(self, project_root: Path):
        """Test ending a trial."""
        expected_usage = {
            "input_tokens": 5000,
            "output_tokens": 2000,
            "total_tokens": 7000,
            "context_percent": 3.5,
        }

        with patch("context_controller.ClaudeSessionManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_manager.get_token_usage.return_value = expected_usage
            mock_manager_cls.return_value = mock_manager

            controller = ContextController(project_root)
            usage = controller.end_trial()

            assert usage == expected_usage
            mock_manager.get_token_usage.assert_called_once()

    def test_adjust_to_target_success(self, project_root: Path, mock_session_result):
        """Test adjusting context to target range."""
        # Create noise chunks
        for i in range(5):
            chunk_path = project_root / "noise_chunks" / f"chunk_{i}.txt"
            chunk_path.write_text(f"Noise chunk {i}")

        context_values = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]
        context_iter = iter(context_values)

        with patch("context_controller.ClaudeSessionManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_manager.send_message.return_value = mock_session_result
            mock_manager.get_context_percent.side_effect = lambda: next(context_iter)
            mock_manager_cls.return_value = mock_manager

            controller = ContextController(project_root)
            final_percent, chunks_used = controller.adjust_to_target(25, 35)

            assert 25 <= final_percent <= 50  # Stopped when reached target
            assert chunks_used >= 0

    def test_adjust_to_target_overshoot(self, project_root: Path, mock_session_result):
        """Test handling overshoot when adjusting to target."""
        # Create noise chunk
        chunk_path = project_root / "noise_chunks" / "chunk_0.txt"
        chunk_path.write_text("Noise chunk")

        # Single chunk causes overshoot
        context_values = [0.0, 50.0]  # First chunk jumps from 0 to 50
        context_iter = iter(context_values)

        with patch("context_controller.ClaudeSessionManager") as mock_manager_cls:
            mock_manager = MagicMock()
            mock_manager.send_message.return_value = mock_session_result
            mock_manager.get_context_percent.side_effect = lambda: next(context_iter)
            mock_manager_cls.return_value = mock_manager

            controller = ContextController(project_root)
            final_percent, chunks_used = controller.adjust_to_target(25, 35)

            # Should stop on overshoot
            assert final_percent == 50.0
            assert chunks_used == 1


class TestEstimateChunksNeeded:
    """Tests for estimate_chunks_needed function."""

    def test_normal_case(self):
        """Test normal chunk estimation."""
        result = estimate_chunks_needed(30.0, 5.0)
        assert result == 6  # 30 / 5 = 6

    def test_zero_increase_rate(self):
        """Test with zero increase rate."""
        result = estimate_chunks_needed(30.0, 0.0)
        assert result == 0

    def test_negative_increase_rate(self):
        """Test with negative increase rate."""
        result = estimate_chunks_needed(30.0, -5.0)
        assert result == 0

    def test_fractional_result(self):
        """Test that result is truncated to int."""
        result = estimate_chunks_needed(25.0, 4.0)
        assert result == 6  # 25 / 4 = 6.25 -> 6

    def test_high_target(self):
        """Test with high target percentage."""
        result = estimate_chunks_needed(80.0, 10.0)
        assert result == 8
