"""Calibration script for determining context consumption per chunk."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from context_controller import ContextController


class Calibrator:
    """Calibrates noise chunk context consumption."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.controller = ContextController(project_root)
        self.results_file = project_root / "results" / "calibration.json"

    def calibrate(self, num_samples: int = 6) -> dict:
        """
        Measure average context increase per noise chunk.

        Args:
            num_samples: Number of chunks to test

        Returns:
            Dictionary with calibration data including token-based measurements
        """
        self.controller.start_trial()
        baseline = self.controller.get_context_percent()

        measurements = []

        for i in range(num_samples):
            before = self.controller.get_context_percent()

            try:
                result = self.controller.inject_noise_chunk(i)
            except FileNotFoundError:
                print(f"No more chunks available after {i}")
                break

            after = self.controller.get_context_percent()
            increase = after - before

            measurement = {
                "chunk_id": i,
                "before_percent": round(before, 2),
                "after_percent": round(after, 2),
                "increase_percent": round(increase, 2),
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "total_tokens": result.total_tokens,
                "success": result.success,
                "duration_ms": result.duration_ms,
            }
            measurements.append(measurement)

            print(f"Chunk {i}: {before:.1f}% -> {after:.1f}% (+{increase:.2f}%)")
            print(f"  Tokens: input={result.input_tokens}, output={result.output_tokens}")

            if not result.success:
                print(f"  Warning: {result.error}")

            # Stop if context is getting too high
            if after > 85:
                print("Context limit approaching, stopping calibration")
                break

        usage = self.controller.end_trial()

        if not measurements:
            return {"error": "No measurements collected"}

        # Calculate averages
        successful = [m for m in measurements if m["success"]]
        if successful:
            avg_increase = sum(m["increase_percent"] for m in successful) / len(successful)
            avg_input_tokens = sum(m["input_tokens"] for m in successful) / len(successful)
            avg_output_tokens = sum(m["output_tokens"] for m in successful) / len(successful)
            avg_total_tokens = sum(m["total_tokens"] for m in successful) / len(successful)
        else:
            avg_increase = 0
            avg_input_tokens = 0
            avg_output_tokens = 0
            avg_total_tokens = 0

        calibration_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "baseline": baseline,
            "num_samples": len(measurements),
            "successful_samples": len(successful),
            "measurements": measurements,
            "average_increase_percent": round(avg_increase, 3),
            "average_input_tokens_per_chunk": round(avg_input_tokens, 0),
            "average_output_tokens_per_chunk": round(avg_output_tokens, 0),
            "average_total_tokens_per_chunk": round(avg_total_tokens, 0),
            "final_usage": usage,
        }

        self.save_results(calibration_data)
        return calibration_data

    def save_results(self, results: dict) -> None:
        """Save calibration results to file."""
        self.results_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.results_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"Calibration results saved to {self.results_file}")

    def load_results(self) -> Optional[dict]:
        """Load previous calibration results."""
        if not self.results_file.exists():
            return None

        with open(self.results_file, "r") as f:
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
    if existing and "error" not in existing:
        print("Previous calibration found:")
        print(f"  Average increase per chunk: {existing.get('average_increase_percent', 0):.2f}%")
        print(f"  Average tokens per chunk: {existing.get('average_total_tokens_per_chunk', 0):.0f}")
        print(f"  Samples: {existing.get('num_samples', 0)}")
        print()

        response = input("Run new calibration? (y/N): ").strip().lower()
        if response != "y":
            print("Using existing calibration.")
            return

    print("Starting calibration...")
    print("This will send noise chunks to Claude and measure token consumption.")
    print()

    calibration_data = calibrator.calibrate()

    if "error" in calibration_data:
        print(f"Calibration failed: {calibration_data['error']}")
        return

    avg_increase = calibration_data["average_increase_percent"]
    avg_tokens = calibration_data["average_total_tokens_per_chunk"]

    print()
    print("=" * 60)
    print("Calibration Complete")
    print("=" * 60)
    print(f"Average context increase per chunk: {avg_increase:.2f}%")
    print(f"Average tokens per chunk: {avg_tokens:.0f}")
    print()
    print(f"Final token usage:")
    print(f"  Input tokens: {calibration_data['final_usage']['input_tokens']}")
    print(f"  Output tokens: {calibration_data['final_usage']['output_tokens']}")
    print(f"  Context consumed: {calibration_data['final_usage']['context_percent']:.1f}%")

    # Estimate chunks needed for each target level
    print()
    print("Estimated chunks needed for target levels:")
    if avg_increase > 0:
        for target in [30, 50, 80]:
            chunks = int(target / avg_increase)
            tokens_needed = int(chunks * avg_tokens)
            print(f"  {target}%: ~{chunks} chunks (~{tokens_needed:,} tokens)")
    else:
        print("  Unable to estimate (no successful measurements)")


if __name__ == "__main__":
    main()
