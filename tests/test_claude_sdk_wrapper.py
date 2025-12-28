"""Tests for claude_sdk_wrapper.py"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claude_sdk_wrapper import SessionResult, TokenUsage, ClaudeSessionManager


class TestSessionResult:
    """Tests for SessionResult dataclass."""

    def test_create_success_result(self):
        """Test creating a successful result."""
        result = SessionResult(
            success=True,
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            content="Response content",
            session_id="session-123",
            duration_ms=1234,
        )

        assert result.success is True
        assert result.input_tokens == 1000
        assert result.output_tokens == 500
        assert result.total_tokens == 1500
        assert result.content == "Response content"
        assert result.session_id == "session-123"
        assert result.duration_ms == 1234
        assert result.error is None

    def test_create_error_result(self):
        """Test creating an error result."""
        result = SessionResult(
            success=False,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            content="",
            error="Connection failed",
        )

        assert result.success is False
        assert result.error == "Connection failed"
        assert result.session_id is None
        assert result.duration_ms == 0


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_default_values(self):
        """Test default token values."""
        usage = TokenUsage()

        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0

    def test_total_tokens_property(self):
        """Test total_tokens computed property."""
        usage = TokenUsage(input_tokens=1000, output_tokens=500)

        assert usage.total_tokens == 1500

    def test_token_accumulation(self):
        """Test that tokens can be accumulated."""
        usage = TokenUsage()
        usage.input_tokens += 1000
        usage.output_tokens += 500
        usage.input_tokens += 2000
        usage.output_tokens += 1000

        assert usage.input_tokens == 3000
        assert usage.output_tokens == 1500
        assert usage.total_tokens == 4500


class TestClaudeSessionManager:
    """Tests for ClaudeSessionManager class."""

    def test_init(self, project_root: Path):
        """Test manager initialization."""
        manager = ClaudeSessionManager(project_root)

        assert manager.project_root == project_root
        assert manager.cumulative_usage.input_tokens == 0
        assert manager.cumulative_usage.output_tokens == 0
        assert manager._session_id is None
        assert manager.CONTEXT_LIMIT == 200_000

    def test_create_options(self, project_root: Path):
        """Test SDK options creation."""
        manager = ClaudeSessionManager(project_root)
        options = manager._create_options()

        assert str(project_root) in str(options.cwd)
        assert "Read" in options.allowed_tools
        assert "Write" in options.allowed_tools
        assert options.permission_mode == "acceptEdits"

    def test_reset_usage(self, project_root: Path):
        """Test resetting token usage."""
        manager = ClaudeSessionManager(project_root)
        manager.cumulative_usage.input_tokens = 5000
        manager.cumulative_usage.output_tokens = 2000
        manager._session_id = "old-session"

        manager.reset_usage()

        assert manager.cumulative_usage.input_tokens == 0
        assert manager.cumulative_usage.output_tokens == 0
        assert manager._session_id is None

    def test_get_context_percent(self, project_root: Path):
        """Test context percentage calculation."""
        manager = ClaudeSessionManager(project_root)
        manager.cumulative_usage.input_tokens = 40000
        manager.cumulative_usage.output_tokens = 10000

        percent = manager.get_context_percent()

        # (40000 + 10000) / 200000 * 100 = 25%
        assert percent == 25.0

    def test_get_context_percent_zero(self, project_root: Path):
        """Test context percentage with no usage."""
        manager = ClaudeSessionManager(project_root)

        percent = manager.get_context_percent()

        assert percent == 0.0

    def test_get_token_usage(self, project_root: Path):
        """Test getting detailed token usage."""
        manager = ClaudeSessionManager(project_root)
        manager.cumulative_usage.input_tokens = 10000
        manager.cumulative_usage.output_tokens = 5000
        manager._session_id = "test-session"

        usage = manager.get_token_usage()

        assert usage["input_tokens"] == 10000
        assert usage["output_tokens"] == 5000
        assert usage["total_tokens"] == 15000
        assert usage["context_percent"] == 7.5  # 15000 / 200000 * 100
        assert usage["session_id"] == "test-session"


class TestClaudeSessionManagerAsync:
    """Tests for async methods in ClaudeSessionManager."""

    @pytest.fixture
    def mock_sdk_messages(self):
        """Create mock SDK message types."""
        # Mock the message types
        mock_text_block = MagicMock()
        mock_text_block.text = "Response text"

        mock_assistant_msg = MagicMock()
        mock_assistant_msg.content = [mock_text_block]

        mock_result_msg = MagicMock()
        mock_result_msg.usage = {"input_tokens": 1000, "output_tokens": 500}
        mock_result_msg.session_id = "session-123"
        mock_result_msg.is_error = False
        mock_result_msg.duration_ms = 2000

        return mock_assistant_msg, mock_result_msg, mock_text_block

    @pytest.mark.asyncio
    async def test_send_message_async_success(self, project_root: Path, mock_sdk_messages):
        """Test successful async message sending."""
        mock_assistant_msg, mock_result_msg, mock_text_block = mock_sdk_messages

        async def mock_query(*args, **kwargs):
            yield mock_assistant_msg
            yield mock_result_msg

        with patch("claude_sdk_wrapper.query", mock_query):
            with patch("claude_sdk_wrapper.TextBlock", type(mock_text_block)):
                with patch("claude_sdk_wrapper.AssistantMessage", type(mock_assistant_msg)):
                    with patch("claude_sdk_wrapper.ResultMessage", type(mock_result_msg)):
                        manager = ClaudeSessionManager(project_root)
                        result = await manager._send_message_async("Test prompt")

                        assert result.success is True
                        assert result.input_tokens == 1000
                        assert result.output_tokens == 500
                        assert result.session_id == "session-123"

    @pytest.mark.asyncio
    async def test_send_message_async_no_result(self, project_root: Path):
        """Test async message when no result is received."""
        mock_assistant_msg = MagicMock()
        mock_assistant_msg.content = []

        async def mock_query(*args, **kwargs):
            yield mock_assistant_msg

        with patch("claude_sdk_wrapper.query", mock_query):
            with patch("claude_sdk_wrapper.AssistantMessage", type(mock_assistant_msg)):
                manager = ClaudeSessionManager(project_root)
                result = await manager._send_message_async("Test prompt")

                assert result.success is False
                assert "No result message" in result.error

    @pytest.mark.asyncio
    async def test_send_message_async_sdk_error(self, project_root: Path):
        """Test handling SDK errors."""
        from claude_code_sdk import ClaudeSDKError

        async def mock_query(*args, **kwargs):
            raise ClaudeSDKError("API error")
            yield  # Make it a generator

        with patch("claude_sdk_wrapper.query", mock_query):
            manager = ClaudeSessionManager(project_root)
            result = await manager._send_message_async("Test prompt")

            assert result.success is False
            assert "ClaudeSDKError" in result.error

    @pytest.mark.asyncio
    async def test_send_message_async_unexpected_error(self, project_root: Path):
        """Test handling unexpected errors."""
        async def mock_query(*args, **kwargs):
            raise RuntimeError("Unexpected error")
            yield

        with patch("claude_sdk_wrapper.query", mock_query):
            manager = ClaudeSessionManager(project_root)
            result = await manager._send_message_async("Test prompt")

            assert result.success is False
            assert "Unexpected error" in result.error


class TestClaudeSessionManagerRetry:
    """Tests for retry logic in ClaudeSessionManager."""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, project_root: Path):
        """Test retry on rate limit error."""
        call_count = 0

        async def mock_send_async(prompt):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return SessionResult(
                    success=False,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    content="",
                    error="Rate limit exceeded",
                )
            return SessionResult(
                success=True,
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                content="Success",
                session_id="session-123",
                duration_ms=1000,
            )

        with patch("asyncio.sleep", new_callable=AsyncMock):
            manager = ClaudeSessionManager(project_root)
            manager._send_message_async = mock_send_async

            result = await manager._send_message_with_retry("Test")

            assert result.success is True
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable_error(self, project_root: Path):
        """Test no retry on non-retryable errors."""
        call_count = 0

        async def mock_send_async(prompt):
            nonlocal call_count
            call_count += 1
            return SessionResult(
                success=False,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                content="",
                error="Invalid prompt",
            )

        manager = ClaudeSessionManager(project_root)
        manager._send_message_async = mock_send_async

        result = await manager._send_message_with_retry("Test")

        assert result.success is False
        assert call_count == 1  # No retry

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, project_root: Path):
        """Test failure after max retries."""
        call_count = 0

        async def mock_send_async(prompt):
            nonlocal call_count
            call_count += 1
            return SessionResult(
                success=False,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                content="",
                error="Rate limit exceeded",
            )

        with patch("asyncio.sleep", new_callable=AsyncMock):
            manager = ClaudeSessionManager(project_root)
            manager._send_message_async = mock_send_async

            result = await manager._send_message_with_retry("Test")

            assert result.success is False
            assert call_count == manager.MAX_RETRIES
            assert "Failed after" in result.error


class TestClaudeSessionManagerSync:
    """Tests for synchronous wrapper method."""

    def test_send_message_sync(self, project_root: Path):
        """Test synchronous message sending."""
        expected_result = SessionResult(
            success=True,
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            content="Response",
            session_id="session-123",
            duration_ms=1000,
        )

        async def mock_send_with_retry(prompt):
            return expected_result

        with patch.object(
            ClaudeSessionManager, "_send_message_with_retry", mock_send_with_retry
        ):
            manager = ClaudeSessionManager(project_root)
            result = manager.send_message("Test prompt")

            assert result == expected_result
