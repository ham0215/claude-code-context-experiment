"""Calibration script for determining context consumption per chunk."""

import json
import time
from pathlib import Path
from typing import Optional
from context_controller import ContextController


class Calibrator:
    """Calibrates noise chunk context consumption."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.controller = ContextController(project_root)
        self.results_file = project_root / "results" / "calibration.json"

    def calibrate(self, num_samples: int = 10) -> float:
        """
        Measure average context increase per noise chunk.

        Args:
            num_samples: Number of chunks to test

        Returns:
            Average context percentage increase per chunk
        """
        self.controller.clear_context()
        baseline = self.controller.get_context_percent()

        increases = []

        for i in range(num_samples):
            before = self.controller.get_context_percent()
            success = self.controller.inject_noise_chunk(i)

            if not success:
                print(f"Failed to inject chunk {i}")
                break

            after = self.controller.get_context_percent()
            increase = after - before
            increases.append(increase)

            print(f"Chunk {i}: {before:.1f}% -> {after:.1f}% (+{increase:.2f}%)")

            # Stop if context is getting too high
            if after > 85:
                print("Context limit approaching, stopping calibration")
                break

        if not increases:
            return 0.0

        avg_increase = sum(increases) / len(increases)

        # Save calibration results
        self.save_results({
            "baseline": baseline,
            "num_samples": len(increases),
            "increases": increases,
            "average_increase": avg_increase
        })

        return avg_increase

    def save_results(self, results: dict) -> None:
        """Save calibration results to file."""
        self.results_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Calibration results saved to {self.results_file}")

    def load_results(self) -> Optional[dict]:
        """Load previous calibration results."""
        if not self.results_file.exists():
            return None

        with open(self.results_file, 'r') as f:
            return json.load(f)


def main():
    """Run calibration."""
    project_root = Path(__file__).parent.parent
    calibrator = Calibrator(project_root)

    print("=" * 60)
    print("Context Consumption Calibration")
    print("=" * 60)
    print()

    # Check for existing calibration
    existing = calibrator.load_results()
    if existing:
        print(f"Previous calibration found:")
        print(f"  Average increase per chunk: {existing['average_increase']:.2f}%")
        print(f"  Samples: {existing['num_samples']}")
        print()

        response = input("Run new calibration? (y/N): ").strip().lower()
        if response != 'y':
            print("Using existing calibration.")
            return

    print("Starting calibration...")
    print()

    avg_increase = calibrator.calibrate()

    print()
    print("=" * 60)
    print("Calibration Complete")
    print("=" * 60)
    print(f"Average context increase per chunk: {avg_increase:.2f}%")

    # Estimate chunks needed for each target level
    print()
    print("Estimated chunks needed:")
    for target in [30, 50, 80]:
        chunks = int(target / avg_increase) if avg_increase > 0 else "N/A"
        print(f"  {target}%: ~{chunks} chunks")


if __name__ == "__main__":
    main()
