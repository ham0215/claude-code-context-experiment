"""Generate CLAUDE.md files with noise content for context consumption experiments.

This script creates level-specific CLAUDE.md files by concatenating noise chunks.
The CLAUDE.md files are placed in workspace directories so they are automatically
loaded as non-compressible system context when subagents access files in those directories.

Usage:
    python scripts/generate_context_claudemd.py --level 80 --chunks 128
    python scripts/generate_context_claudemd.py --level 50 --chunks 80
    python scripts/generate_context_claudemd.py --level 30 --chunks 48
    python scripts/generate_context_claudemd.py --all
"""

import argparse
from pathlib import Path

# Default chunk counts per level (from calibration)
LEVEL_CHUNKS = {
    "30": 48,
    "50": 80,
    "80": 128,
}

PROJECT_ROOT = Path(__file__).parent.parent
NOISE_DIR = PROJECT_ROOT / "noise_chunks"
WORKSPACES_DIR = PROJECT_ROOT / "workspaces"


def generate_claudemd(level: str, num_chunks: int) -> Path:
    """Generate a CLAUDE.md file for a given context level.

    Args:
        level: Context level string (e.g., "30", "50", "80")
        num_chunks: Number of noise chunks to concatenate

    Returns:
        Path to the generated CLAUDE.md file
    """
    workspace_dir = WORKSPACES_DIR / f"trial_{level}%"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Concatenate noise chunks
    parts = []
    parts.append(f"# Context Noise for {level}% Level Experiment\n")
    parts.append(f"# Chunks: {num_chunks} | Target: ~{level}% context consumption\n")
    parts.append("# This content is auto-generated for experiment purposes.\n\n")

    for i in range(num_chunks):
        chunk_file = NOISE_DIR / f"chunk_{i}.txt"
        if not chunk_file.exists():
            print(f"WARNING: {chunk_file} not found, stopping at {i} chunks")
            break
        parts.append(f"--- Chunk {i} ---\n")
        parts.append(chunk_file.read_text())
        parts.append("\n\n")

    content = "".join(parts)
    output_path = workspace_dir / "CLAUDE.md"
    output_path.write_text(content)

    size_bytes = len(content.encode("utf-8"))
    estimated_tokens = size_bytes // 4

    print(f"Generated: {output_path}")
    print(f"  Chunks: {num_chunks}")
    print(f"  Size: {size_bytes:,} bytes (~{estimated_tokens:,} tokens)")
    print(f"  Estimated context: ~{estimated_tokens / 200_000 * 100:.1f}%")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate CLAUDE.md files with noise for context experiments"
    )
    parser.add_argument(
        "--level", type=str, choices=["30", "50", "80"],
        help="Context level (30, 50, or 80)"
    )
    parser.add_argument(
        "--chunks", type=int,
        help="Number of noise chunks (overrides default for level)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Generate CLAUDE.md for all levels"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("CLAUDE.md Context Generator")
    print("=" * 60)
    print()

    if not NOISE_DIR.exists():
        print(f"ERROR: Noise chunks directory not found: {NOISE_DIR}")
        print("Run 'python scripts/generate_noise_chunks.py' first.")
        return

    available_chunks = len(list(NOISE_DIR.glob("chunk_*.txt")))
    print(f"Available noise chunks: {available_chunks}")
    print()

    if args.all:
        for level, chunks in LEVEL_CHUNKS.items():
            generate_claudemd(level, chunks)
            print()
    elif args.level:
        chunks = args.chunks or LEVEL_CHUNKS[args.level]
        generate_claudemd(args.level, chunks)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
