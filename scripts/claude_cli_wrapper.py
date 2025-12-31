"""Wrapper for Claude Code CLI with session continuation."""

import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SessionResult:
    """Result from a CLI interaction."""

    success: bool
    content: str
    session_id: Optional[str] = None
    error: Optional[str] = None
    duration_ms: int = 0


class ClaudeCLISessionManager:
    """Manages Claude Code CLI sessions with continuation."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.session_id: Optional[str] = None
        self.message_count = 0
        self._estimated_tokens = 0

    def reset_session(self) -> None:
        """Reset session for new trial."""
        self.session_id = None
        self.message_count = 0
        self._estimated_tokens = 0

    def send_message(self, prompt: str, timeout: int = 120) -> SessionResult:
        """
        Send a message using Claude Code CLI.

        Args:
            prompt: The message to send
            timeout: Timeout in seconds

        Returns:
            SessionResult with response
        """
        start_time = time.time()

        # Build command
        cmd = ["claude", "--print"]

        # Use session continuation if we have a session ID
        if self.session_id:
            cmd.extend(["--resume", self.session_id])

        cmd.extend(["-p", prompt])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=timeout,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Extract session ID from output if present
            # Claude CLI outputs session info in certain formats
            output = result.stdout

            # Try to extract session ID from the output
            session_match = re.search(r'session[_-]?id["\s:]+([a-f0-9-]+)', output, re.I)
            if session_match:
                self.session_id = session_match.group(1)

            # If no explicit session ID, try to get from stderr or use a marker
            if not self.session_id and result.returncode == 0:
                # Generate a pseudo session ID based on first successful call
                self.session_id = f"session_{int(time.time())}"

            self.message_count += 1
            # Estimate tokens (rough: 4 chars per token for prompt + response)
            self._estimated_tokens += (len(prompt) + len(output)) // 4

            if result.returncode != 0:
                return SessionResult(
                    success=False,
                    content=output,
                    session_id=self.session_id,
                    error=result.stderr or f"Exit code: {result.returncode}",
                    duration_ms=duration_ms,
                )

            return SessionResult(
                success=True,
                content=output,
                session_id=self.session_id,
                duration_ms=duration_ms,
            )

        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            return SessionResult(
                success=False,
                content="",
                error="Timeout",
                duration_ms=duration_ms,
            )
        except FileNotFoundError:
            return SessionResult(
                success=False,
                content="",
                error="Claude CLI not found. Make sure 'claude' is in PATH.",
                duration_ms=0,
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return SessionResult(
                success=False,
                content="",
                error=str(e),
                duration_ms=duration_ms,
            )

    def get_estimated_context_percent(self) -> float:
        """
        Estimate context consumption based on message sizes.

        Returns:
            Estimated context percentage (0-100)
        """
        # 200K token limit
        return (self._estimated_tokens / 200_000) * 100

    def get_token_usage(self) -> dict:
        """Get estimated token usage."""
        return {
            "estimated_tokens": self._estimated_tokens,
            "context_percent": self.get_estimated_context_percent(),
            "message_count": self.message_count,
            "session_id": self.session_id,
        }


if __name__ == "__main__":
    # Test the CLI wrapper
    project_root = Path(__file__).parent.parent

    print("Testing ClaudeCLISessionManager...")
    print(f"Project root: {project_root}")

    manager = ClaudeCLISessionManager(project_root)

    # Test a simple message
    print("\nSending test message...")
    result = manager.send_message("Say 'Hello' and nothing else.")

    if result.success:
        print(f"Response: {result.content[:200]}...")
        print(f"Session ID: {result.session_id}")
        print(f"Duration: {result.duration_ms}ms")
    else:
        print(f"Error: {result.error}")

    print(f"\nEstimated context: {manager.get_estimated_context_percent():.2f}%")
