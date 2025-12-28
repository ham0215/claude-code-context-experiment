"""Wrapper for Claude Agent SDK to provide sync interface and token tracking."""

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from claude_code_sdk import query, ClaudeSDKError
from claude_code_sdk.types import (
    ClaudeCodeOptions,
    Message,
    AssistantMessage,
    ResultMessage,
    ContentBlock,
    TextBlock,
)


@dataclass
class SessionResult:
    """Result from a Claude session interaction."""

    success: bool
    input_tokens: int
    output_tokens: int
    total_tokens: int
    content: str
    error: Optional[str] = None
    session_id: Optional[str] = None
    duration_ms: int = 0


@dataclass
class TokenUsage:
    """Token usage tracking."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class ClaudeSessionManager:
    """Manages Claude SDK sessions with token tracking."""

    CONTEXT_LIMIT = 200_000  # 200K token limit
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 5

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.cumulative_usage = TokenUsage()
        self._session_id: Optional[str] = None

    def _create_options(self) -> ClaudeCodeOptions:
        """Create SDK options for the experiment."""
        return ClaudeCodeOptions(
            cwd=str(self.project_root),
            allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
            permission_mode="acceptEdits",
        )

    async def _send_message_async(self, prompt: str) -> SessionResult:
        """Send a message and collect response with usage info."""
        options = self._create_options()

        content_parts = []
        result_message: Optional[ResultMessage] = None
        input_tokens = 0
        output_tokens = 0

        try:
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            content_parts.append(block.text)
                elif isinstance(message, ResultMessage):
                    result_message = message

            if result_message is None:
                return SessionResult(
                    success=False,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    content="",
                    error="No result message received",
                )

            # Extract usage from result (usage is a dict)
            if result_message.usage:
                input_tokens = result_message.usage.get("input_tokens", 0) or 0
                output_tokens = result_message.usage.get("output_tokens", 0) or 0

            self.cumulative_usage.input_tokens += input_tokens
            self.cumulative_usage.output_tokens += output_tokens
            self._session_id = result_message.session_id

            return SessionResult(
                success=not result_message.is_error,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                content="\n".join(content_parts),
                session_id=result_message.session_id,
                duration_ms=result_message.duration_ms or 0,
            )

        except ClaudeSDKError as e:
            return SessionResult(
                success=False,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                content="",
                error=f"ClaudeSDKError: {e}",
            )
        except Exception as e:
            return SessionResult(
                success=False,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                content="",
                error=f"Unexpected error: {e}",
            )

    async def _send_message_with_retry(self, prompt: str) -> SessionResult:
        """Send message with retry logic for transient failures."""
        last_error: Optional[str] = None

        for attempt in range(self.MAX_RETRIES):
            result = await self._send_message_async(prompt)

            if result.success:
                return result

            # Check if error is retryable
            if result.error and ("rate" in result.error.lower() or "timeout" in result.error.lower()):
                last_error = result.error
                print(f"Retryable error (attempt {attempt + 1}): {result.error}")
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY_SECONDS * (attempt + 1)
                    print(f"Waiting {delay}s before retry...")
                    await asyncio.sleep(delay)
            else:
                # Non-retryable error
                return result

        return SessionResult(
            success=False,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            content="",
            error=f"Failed after {self.MAX_RETRIES} attempts: {last_error}",
        )

    def reset_usage(self) -> None:
        """Reset cumulative token usage for new trial."""
        self.cumulative_usage = TokenUsage()
        self._session_id = None

    def send_message(self, prompt: str) -> SessionResult:
        """Send a message synchronously with retry."""
        return asyncio.run(self._send_message_with_retry(prompt))

    def get_context_percent(self) -> float:
        """Calculate current context consumption percentage."""
        total_context = self.cumulative_usage.total_tokens
        return (total_context / self.CONTEXT_LIMIT) * 100

    def get_token_usage(self) -> dict:
        """Get detailed token usage."""
        return {
            "input_tokens": self.cumulative_usage.input_tokens,
            "output_tokens": self.cumulative_usage.output_tokens,
            "total_tokens": self.cumulative_usage.total_tokens,
            "context_percent": self.get_context_percent(),
            "session_id": self._session_id,
        }
