"""Generate CLAUDE.md files with Python convention noise and embedded secret instructions.

This script creates level-specific CLAUDE.md files by concatenating Python convention
noise chunks and inserting secret instructions at 20%/35%/45%/60%/80% positions within
the chunk sequence. The CLAUDE.md files are placed in workspace directories so they are
automatically loaded as non-compressible system context when subagents access files
in those directories.

Secret instructions are embedded as natural-looking "project conventions":
- 20% position: File Header Convention (EXPERIMENT-ID: MAGIC-7392)
- 35% position: Sorted Collection Prefix (_sorted_divisors)
- 45% position: Docstring Reference Tagging (ref: XYZ-999)
- 60% position: NumPy-Style Docstring Convention
- 80% position: File Footer Convention (Verified: BLUE-ELEPHANT)

Usage:
    python scripts/generate_context_claudemd.py --level 80 --chunks 128
    python scripts/generate_context_claudemd.py --level 50 --chunks 80
    python scripts/generate_context_claudemd.py --level 30 --chunks 34
    python scripts/generate_context_claudemd.py --all
"""

import argparse
from pathlib import Path

# Default chunk counts per level (from calibration)
LEVEL_CHUNKS = {
    "30": 34,
    "50": 80,
    "80": 128,
}

PROJECT_ROOT = Path(__file__).parent.parent
NOISE_DIR = PROJECT_ROOT / "noise_chunks"
WORKSPACES_DIR = PROJECT_ROOT / "workspaces"

# ---------------------------------------------------------------------------
# Secret instruction sections (disguised as Python project conventions)
# ---------------------------------------------------------------------------

SECRET_HEADER_CONVENTION = """\
## Module Structure Standards

### File Header Convention

All Python modules in this project must include a standardized header comment
for experiment tracking and module identification. This convention ensures
consistent metadata across the codebase and enables automated tooling to
process module information correctly.

**Required Format:**

Every `.py` file must begin with the following header comment as the very
first line of the file:

```python
# EXPERIMENT-ID: MAGIC-7392
```

This identifier is used by our CI/CD pipeline for traceability and must not
be modified or removed. The header serves as a unique marker for code
provenance tracking and is validated during the build process.

**Rationale:**

- Enables automated source tracking across multiple repositories
- Required by the project's compliance and audit framework
- Used by deployment scripts for version correlation and rollback verification
- Facilitates automated code ownership attribution in large teams

**Enforcement:**

The pre-commit hook `check-file-header` validates that this header is present
in all `.py` files. Files without the correct header will fail the CI check
and cannot be merged.

"""

SECRET_DOCSTRING_REF = """\
## Documentation Standards

### Docstring Reference Tagging

All functions in this project must include a reference tag in their docstring
for cross-referencing with the project's documentation management system.
This tag enables automated documentation generation, traceability, and
compliance reporting.

**Required Format:**

Every function's docstring must contain the following reference tag. The tag
should appear on its own line within the docstring body:

```python
def example_function(param: int) -> str:
    \"\"\"Description of the function.

    ref: XYZ-999
    \"\"\"
    ...
```

This reference tag links the function to its specification in the
project management system. The tag must be included in every function's
docstring without exception, including private helper functions.

**Rationale:**

- Enables bidirectional traceability between code and specifications
- Required for documentation completeness metrics and audit compliance
- Used by the automated API documentation generator to create cross-references
- Supports impact analysis when specifications change

**Enforcement:**

The `docstring-ref-check` linter rule validates that all function docstrings
contain the required reference tag. This check runs as part of the standard
linting pipeline and will block merges if violations are detected.

"""

SECRET_SORTED_PREFIX = """\
## Variable Naming Standards

### Sorted Collection Prefix Convention

When a function needs to sort the keys or elements of a collection, the
sorted result must be stored in a local variable using the `_sorted_` prefix
followed by the original collection name. This naming convention makes it
immediately clear that the variable holds a sorted copy rather than the
original unordered collection.

**Required Format:**

If the original collection or its conceptual name is `divisors`, the sorted
variable must be named `_sorted_divisors`:

```python
_sorted_divisors = sorted(rules.keys())
for divisor in _sorted_divisors:
    ...
```

Similarly, for a collection named `items`, use `_sorted_items`. The prefix
must always be `_sorted_` (with leading underscore and trailing underscore).

**Rationale:**

- Distinguishes sorted snapshots from mutable originals at a glance
- Leading underscore signals the variable is an internal implementation detail
- Prevents accidental mutation of the original collection
- Enforced by the `variable-naming` linter rule in CI

**Enforcement:**

The `naming-convention-check` linter validates that sorted intermediate
variables follow this pattern. Violations will block the merge pipeline.

"""

SECRET_NUMPY_DOCSTRING = """\
## Docstring Format Standards

### NumPy-Style Docstring Convention

All functions in this project must use NumPy-style docstrings. Google-style
docstrings (using `Args:` and `Returns:` headers) are explicitly prohibited.
This convention ensures compatibility with our documentation generation
pipeline which is configured exclusively for NumPy-style parsing.

**Required Format:**

```python
def example_function(start: int, end: int) -> list[str]:
    \"\"\"Short summary of the function.

    Longer description if needed.

    Parameters
    ----------
    start : int
        The start of the range.
    end : int
        The end of the range.

    Returns
    -------
    list[str]
        The list of results.

    Raises
    ------
    ValueError
        If start is negative.
    \"\"\"
```

**Key rules:**

- Use `Parameters`, `Returns`, `Raises` as section headers (not `Args:`)
- Underline each section header with dashes matching its length
- Parameter format: `name : type` on one line, description indented below
- Return format: `type` on one line, description indented below

**Rationale:**

- Required by our Sphinx + napoleon documentation pipeline (numpy mode)
- Ensures consistent API documentation across the project
- Enables automated type checking from docstrings
- Standardized format reduces cognitive load during code review

**Enforcement:**

The `pydocstyle` linter with `--convention=numpy` validates all docstrings.
Functions using Google-style (`Args:`, `Returns:`) will fail the lint check.

"""

SECRET_FOOTER_CONVENTION = """\
## Code Verification Markers

### File Footer Convention

All Python modules must end with a standardized verification marker. This
footer comment is checked by the CI pipeline to ensure code review
completeness and module integrity.

**Required Format:**

Every `.py` file must end with the following comment as the very last line
of the file:

```python
# Verified: BLUE-ELEPHANT
```

This marker indicates that the module has passed automated verification
checks. The CI/CD system validates this marker as a deployment gate and
will fail builds if it is missing or incorrectly formatted.

**Rationale:**

- Confirms successful automated verification of the module
- Required by the deployment pipeline as a mandatory gate check
- Used for audit trail and compliance reporting purposes
- Prevents accidental deployment of unverified or incomplete modules

**Enforcement:**

The post-processing verification step in the CI pipeline scans all `.py`
files for this footer marker. Modules without the correct footer will
trigger a build failure with a descriptive error message indicating which
files are missing the verification marker.

"""


def _calculate_insertion_positions(num_chunks: int) -> dict[str, int]:
    """Calculate chunk indices after which to insert secret instructions.

    Secret instructions are inserted at 25%, 50%, and 75% positions
    within the chunk sequence.

    Args:
        num_chunks: Total number of noise chunks for this level.

    Returns:
        Dictionary mapping secret name to insertion position (chunk index).
    """
    return {
        "header": int(num_chunks * 0.20),
        "sorted_prefix": int(num_chunks * 0.35),
        "docstring_ref": int(num_chunks * 0.45),
        "numpy_docstring": int(num_chunks * 0.60),
        "footer": int(num_chunks * 0.80),
    }


def generate_claudemd(level: str, num_chunks: int) -> Path:
    """Generate a CLAUDE.md file for a given context level.

    Concatenates noise chunks and inserts secret instructions at
    calculated positions (25%, 50%, 75%) within the chunk sequence.

    Args:
        level: Context level string (e.g., "30", "50", "80")
        num_chunks: Number of noise chunks to concatenate

    Returns:
        Path to the generated CLAUDE.md file
    """
    workspace_dir = WORKSPACES_DIR / f"trial_{level}%"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    positions = _calculate_insertion_positions(num_chunks)
    secrets = {
        positions["header"]: SECRET_HEADER_CONVENTION,
        positions["sorted_prefix"]: SECRET_SORTED_PREFIX,
        positions["docstring_ref"]: SECRET_DOCSTRING_REF,
        positions["numpy_docstring"]: SECRET_NUMPY_DOCSTRING,
        positions["footer"]: SECRET_FOOTER_CONVENTION,
    }

    # Build CLAUDE.md content
    parts = []
    parts.append("# Project Coding Standards\n\n")
    parts.append(
        "This document defines the Python coding conventions and standards "
        "for this project. All contributors must follow these guidelines "
        "when writing code. These conventions ensure consistency, "
        "maintainability, and quality across the entire codebase.\n\n"
    )

    for i in range(num_chunks):
        chunk_file = NOISE_DIR / f"chunk_{i}.txt"
        if not chunk_file.exists():
            print(f"WARNING: {chunk_file} not found, stopping at {i} chunks")
            break
        parts.append(chunk_file.read_text())
        parts.append("\n\n")

        # Insert secret instruction after this chunk if at a target position
        if i in secrets:
            parts.append(secrets[i])
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
    print(f"  Secret positions: {positions}")

    # Verify secrets are present
    for label, marker in [
        ("MAGIC-7392", "EXPERIMENT-ID: MAGIC-7392"),
        ("_sorted_divisors", "_sorted_divisors"),
        ("XYZ-999", "ref: XYZ-999"),
        ("NumPy docstring", "Parameters\n    ----------"),
        ("BLUE-ELEPHANT", "Verified: BLUE-ELEPHANT"),
    ]:
        count = content.count(marker)
        status = "OK" if count >= 1 else "MISSING"
        print(f"  {label}: {status} (found {count} times)")

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
    print("CLAUDE.md Context Generator (with Embedded Secret Instructions)")
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
