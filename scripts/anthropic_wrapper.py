"""Wrapper for Anthropic API with message history management for context experiments."""

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class SessionResult:
    """Result from an API interaction."""

    success: bool
    input_tokens: int
    output_tokens: int
    total_tokens: int
    content: str
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class ConversationMessage:
    """A message in the conversation history."""
    role: str  # "user" or "assistant"
    content: str


class AnthropicSessionManager:
    """Manages Anthropic API sessions with persistent message history."""

    CONTEXT_LIMIT = 200_000  # 200K token limit
    MODEL = "claude-sonnet-4-20250514"  # Use Claude Sonnet for experiments
    MAX_TOKENS = 4096

    def __init__(self, project_root: Path):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )

        self.project_root = project_root
        self.client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

        # Conversation state
        self.messages: list[dict] = []
        self.cumulative_input_tokens = 0
        self.cumulative_output_tokens = 0

        # System prompt for implementation tasks
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load system prompt for the experiment."""
        prompt_path = self.project_root / "prompts" / "system_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text()

        # Default system prompt
        return f"""You are a Python developer assistant. Your task is to implement code based on requirements.

Working directory: {self.project_root}

When asked to implement something:
1. Create the required Python file
2. Follow best practices and PEP 8
3. Include all specified functions
4. Do not add extra commentary, just provide the code

Important: Always read any reference material provided carefully and follow the instructions exactly."""

    def reset_conversation(self) -> None:
        """Reset conversation for new trial."""
        self.messages = []
        self.cumulative_input_tokens = 0
        self.cumulative_output_tokens = 0

    def send_message(self, content: str) -> SessionResult:
        """Send a message and get response, maintaining conversation history."""
        start_time = time.time()

        # Add user message to history
        self.messages.append({"role": "user", "content": content})

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=self.system_prompt,
                messages=self.messages,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Extract response content
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text

            # Add assistant response to history
            self.messages.append({"role": "assistant", "content": response_text})

            # Track token usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            self.cumulative_input_tokens += input_tokens
            self.cumulative_output_tokens += output_tokens

            return SessionResult(
                success=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                content=response_text,
                duration_ms=duration_ms,
            )

        except anthropic.APIError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            # Remove the failed user message
            self.messages.pop()
            return SessionResult(
                success=False,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                content="",
                error=f"API Error: {e}",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.messages.pop()
            return SessionResult(
                success=False,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                content="",
                error=f"Unexpected error: {e}",
                duration_ms=duration_ms,
            )

    def get_context_percent(self) -> float:
        """Calculate current context consumption percentage."""
        total_tokens = self.cumulative_input_tokens + self.cumulative_output_tokens
        return (total_tokens / self.CONTEXT_LIMIT) * 100

    def get_token_usage(self) -> dict:
        """Get detailed token usage."""
        return {
            "input_tokens": self.cumulative_input_tokens,
            "output_tokens": self.cumulative_output_tokens,
            "total_tokens": self.cumulative_input_tokens + self.cumulative_output_tokens,
            "context_percent": self.get_context_percent(),
            "message_count": len(self.messages),
        }

    def get_estimated_context_tokens(self) -> int:
        """
        Estimate total context tokens that would be sent in next request.
        This includes system prompt + all messages in history.
        """
        # Rough estimation: 4 chars per token
        system_tokens = len(self.system_prompt) // 4
        message_tokens = sum(len(m["content"]) // 4 for m in self.messages)
        return system_tokens + message_tokens


if __name__ == "__main__":
    # Test the wrapper
    project_root = Path(__file__).parent.parent

    print("Testing AnthropicSessionManager...")
    print(f"Project root: {project_root}")

    try:
        manager = AnthropicSessionManager(project_root)
        print("Manager initialized successfully")

        # Test a simple message
        result = manager.send_message("Say 'Hello' and nothing else.")
        print(f"Response: {result.content}")
        print(f"Tokens: input={result.input_tokens}, output={result.output_tokens}")
        print(f"Context: {manager.get_context_percent():.2f}%")

    except ImportError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
