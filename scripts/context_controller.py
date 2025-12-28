"""Context controller for managing Claude Code context consumption."""

import subprocess
import time
import re
from pathlib import Path
from typing import Optional


class ContextController:
    """Controls context consumption for Claude Code experiments."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.noise_chunks_dir = project_root / "noise_chunks"
        self.chunk_increase_rate: Optional[float] = None

    def get_context_percent(self) -> float:
        """
        Get current context consumption percentage from Claude Code.

        Note: This is a placeholder. In actual implementation,
        this would need to interact with Claude Code CLI or API
        to get the current context usage.

        Returns:
            Current context percentage (0-100)
        """
        # Placeholder - actual implementation would query Claude Code
        # This could be done by parsing the /context command output
        # or through Claude Code's API if available
        return 0.0

    def clear_context(self) -> bool:
        """
        Clear Claude Code context by running /clear command.

        Returns:
            True if successful, False otherwise
        """
        # Placeholder - actual implementation would send /clear to Claude Code
        return True

    def inject_noise_chunk(self, chunk_id: int) -> bool:
        """
        Inject a noise chunk into the conversation to consume context.

        Args:
            chunk_id: ID of the noise chunk to inject

        Returns:
            True if successful, False otherwise
        """
        chunk_path = self.noise_chunks_dir / f"chunk_{chunk_id}.txt"

        if not chunk_path.exists():
            print(f"Warning: Chunk {chunk_id} does not exist")
            return False

        # Placeholder - actual implementation would send the chunk
        # content to Claude Code through the CLI or API
        return True

    def adjust_to_target(self, target_min: int, target_max: int) -> int:
        """
        Adjust context to target range by injecting noise chunks.

        Args:
            target_min: Minimum target context percentage
            target_max: Maximum target context percentage

        Returns:
            Actual context percentage achieved
        """
        self.clear_context()
        current = self.get_context_percent()
        chunk_id = 0
        max_chunks = 100  # Safety limit

        while current < target_min and chunk_id < max_chunks:
            self.inject_noise_chunk(chunk_id)
            current = self.get_context_percent()
            chunk_id += 1

            # Check for overshoot
            if current > target_max:
                print(f"Overshoot detected: {current}% > {target_max}%")
                # Retry with fresh context
                return self.adjust_to_target(target_min, target_max)

        return int(current)


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
