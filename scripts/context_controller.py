"""Context controller for managing Claude context consumption."""

from pathlib import Path
from typing import Optional

from claude_cli_wrapper import ClaudeCLISessionManager, SessionResult


class ContextController:
    """Controls context consumption for Claude experiments."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.noise_chunks_dir = project_root / "noise_chunks"
        self.prompts_dir = project_root / "prompts"
        self.session_manager = ClaudeCLISessionManager(project_root)
        self._noise_template: Optional[str] = None

    def _load_noise_template(self) -> str:
        """Load noise prompt template."""
        if self._noise_template is None:
            template_path = self.prompts_dir / "noise_prompt_template.txt"
            if template_path.exists():
                self._noise_template = template_path.read_text()
            else:
                # Default template - short acknowledgment request
                self._noise_template = (
                    "Read this reference material and respond with only 'OK':\n\n{noise_content}"
                )
        return self._noise_template

    def get_context_percent(self) -> float:
        """
        Get current context consumption percentage (estimated).

        Returns:
            Estimated context percentage (0-100)
        """
        return self.session_manager.get_estimated_context_percent()

    def clear_context(self) -> bool:
        """
        Clear context by resetting session.

        Returns:
            True if successful
        """
        self.session_manager.reset_session()
        return True

    def inject_noise_chunk(self, chunk_id: int) -> SessionResult:
        """
        Inject a noise chunk into the conversation to consume context.

        Args:
            chunk_id: ID of the noise chunk to inject

        Returns:
            SessionResult with response

        Raises:
            FileNotFoundError: If chunk file doesn't exist
        """
        chunk_path = self.noise_chunks_dir / f"chunk_{chunk_id}.txt"

        if not chunk_path.exists():
            raise FileNotFoundError(f"Chunk {chunk_id} does not exist at {chunk_path}")

        noise_content = chunk_path.read_text()
        template = self._load_noise_template()
        prompt = template.replace("{noise_content}", noise_content)

        return self.session_manager.send_message(prompt)

    def send_implementation_prompt(self, prompt: str) -> SessionResult:
        """
        Send the implementation prompt to Claude.

        Args:
            prompt: The implementation prompt text

        Returns:
            SessionResult with response
        """
        return self.session_manager.send_message(prompt, timeout=180)

    def start_trial(self) -> None:
        """Start a new trial with fresh session."""
        self.session_manager.reset_session()

    def end_trial(self) -> dict:
        """
        End trial and return usage summary.

        Returns:
            Dictionary with usage details
        """
        return self.session_manager.get_token_usage()

    def adjust_to_target(
        self, target_min: int, target_max: int
    ) -> tuple[float, int]:
        """
        Adjust context to target range by injecting noise chunks.

        Args:
            target_min: Minimum target context percentage
            target_max: Maximum target context percentage

        Returns:
            Tuple of (actual context percentage, number of chunks injected)
        """
        chunk_id = 0
        max_chunks = 200  # Safety limit

        current = self.get_context_percent()

        while current < target_min and chunk_id < max_chunks:
            try:
                result = self.inject_noise_chunk(chunk_id)
                if not result.success:
                    print(f"Warning: Chunk {chunk_id} injection failed: {result.error}")
                    break
                current = self.get_context_percent()
                chunk_id += 1

                if chunk_id % 5 == 0:  # Print every 5 chunks to reduce output
                    print(f"  Chunk {chunk_id}: context at {current:.1f}%")

                # Check for overshoot
                if current > target_max:
                    print(f"  Reached target: {current:.1f}%")
                    break

            except FileNotFoundError:
                print(f"No more chunks available after {chunk_id}")
                break

        return current, chunk_id


def estimate_chunks_needed(target_percent: float, chunk_increase_rate: float) -> int:
    """
    Estimate how many chunks are needed to reach target context level.

    Args:
        target_percent: Target context percentage
        chunk_increase_rate: Percentage increase per chunk

    Returns:
        Estimated number of chunks needed
    """
    if chunk_increase_rate <= 0:
        return 0
    return int(target_percent / chunk_increase_rate)


if __name__ == "__main__":
    # Example usage
    project_root = Path(__file__).parent.parent
    controller = ContextController(project_root)

    print("Context Controller initialized")
    print(f"Project root: {project_root}")
    print(f"Noise chunks dir: {controller.noise_chunks_dir}")

    # Check if noise chunks exist
    if controller.noise_chunks_dir.exists():
        chunks = list(controller.noise_chunks_dir.glob("chunk_*.txt"))
        print(f"Found {len(chunks)} noise chunks")
    else:
        print("No noise chunks directory found")

    print(f"Current context: {controller.get_context_percent():.2f}%")
