"""Generate Python convention noise chunks for context consumption experiments.

Creates 200 noise chunks (~5KB each) based on Python coding conventions.
These are used as context filler in CLAUDE.md files for experiment trials.

20 topics x 10 variations = 200 chunks.

Usage:
    python scripts/generate_noise_chunks.py
"""

import re
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
NOISE_DIR = PROJECT_ROOT / "noise_chunks"
TARGET_SIZE_MIN = 4800
TARGET_SIZE_MAX = 5200

# ---------------------------------------------------------------------------
# Topic definitions: (name, description, [10 subtopics], [guidelines])
# ---------------------------------------------------------------------------
TOPICS = [
    (
        "Async/Await Patterns",
        "asynchronous programming with asyncio, covering coroutine design, task orchestration, and concurrent I/O patterns",
        [
            "Coroutine Function Design",
            "Task Groups and Structured Concurrency",
            "Async Context Managers",
            "Error Handling in Async Code",
            "Async Iterators and Generators",
            "Semaphore-Based Rate Limiting",
            "Async Queue Processing",
            "Timeout and Cancellation Patterns",
            "Testing Async Code with pytest-asyncio",
            "Async Database Access Patterns",
        ],
        [
            "Always use `async def` for functions performing I/O operations",
            "Set explicit timeouts for all network and external service calls",
            "Use `async with` for managing async resources such as sessions and connections",
            "Handle `asyncio.CancelledError` explicitly to clean up resources",
            "Prefer `asyncio.TaskGroup` over `asyncio.gather` for structured concurrency",
            "Avoid blocking calls inside async functions; use `asyncio.to_thread` for CPU-bound work",
            "Use `asyncio.Semaphore` to limit concurrent access to shared resources",
        ],
    ),
    (
        "Django ORM Conventions",
        "Django ORM usage patterns including model design, queryset optimization, and database interaction conventions",
        [
            "QuerySet Optimization Techniques",
            "Model Field Design Conventions",
            "Custom Manager and QuerySet Methods",
            "Database Migration Best Practices",
            "Transaction Management Patterns",
            "Relationship Modeling Guidelines",
            "Aggregation and Annotation Patterns",
            "Raw SQL Safety Guidelines",
            "Signal Usage Conventions",
            "Model Validation Strategies",
        ],
        [
            "Use `select_related` and `prefetch_related` to avoid N+1 query problems",
            "Define `__str__` on all models for readable admin and debug output",
            "Keep business logic in model methods rather than views",
            "Always provide `verbose_name` and `help_text` on model fields",
            "Use `F()` expressions for database-level operations instead of Python-level computation",
            "Index fields that are frequently used in filters and ordering",
            "Use `bulk_create` and `bulk_update` for batch operations",
        ],
    ),
    (
        "Flask/FastAPI Routing",
        "web framework routing conventions for Flask and FastAPI, including endpoint design, middleware, and request handling",
        [
            "RESTful Endpoint Naming Conventions",
            "Request Validation with Pydantic",
            "Middleware and Hook Patterns",
            "Dependency Injection in FastAPI",
            "Blueprint and Router Organization",
            "Error Response Standardization",
            "File Upload Handling Conventions",
            "WebSocket Endpoint Design",
            "API Versioning Strategies",
            "Authentication Middleware Patterns",
        ],
        [
            "Use plural nouns for resource endpoints (e.g., `/users`, `/orders`)",
            "Return consistent error response structures with `detail` and `status_code`",
            "Validate all request bodies using Pydantic models or marshmallow schemas",
            "Group related endpoints into blueprints or routers by domain",
            "Use dependency injection for shared resources like database sessions",
            "Apply rate limiting middleware to public-facing endpoints",
            "Document all endpoints with OpenAPI-compatible docstrings",
        ],
    ),
    (
        "Database Connection Management",
        "database connection pooling, lifecycle management, and health checking conventions for Python applications",
        [
            "Connection Pool Configuration",
            "Connection Lifecycle Management",
            "Health Check and Retry Patterns",
            "Multi-Database Routing Conventions",
            "Read Replica Load Balancing",
            "Connection Timeout Strategies",
            "SSL/TLS Connection Configuration",
            "Connection Monitoring and Metrics",
            "Async Connection Pool Patterns",
            "Connection String Management",
        ],
        [
            "Always use connection pooling in production; never create connections per request",
            "Set `pool_pre_ping` or equivalent health checks to detect stale connections",
            "Configure maximum pool size based on expected concurrent load",
            "Use context managers to ensure connections are returned to the pool",
            "Implement exponential backoff for connection retry logic",
            "Store connection strings in environment variables, never in source code",
            "Monitor connection pool utilization and alert on exhaustion",
        ],
    ),
    (
        "Logging Best Practices",
        "Python logging configuration, structured logging patterns, and observability conventions for production applications",
        [
            "Logger Configuration Standards",
            "Structured Logging with JSON",
            "Log Level Usage Guidelines",
            "Context Propagation in Logs",
            "Performance-Aware Logging",
            "Log Rotation and Retention Policies",
            "Third-Party Log Integration",
            "Error and Exception Logging",
            "Audit Logging Conventions",
            "Testing Log Output",
        ],
        [
            "Use `logging.getLogger(__name__)` to create module-level loggers",
            "Never use `print()` for application logging in production code",
            "Include correlation IDs in all log messages for request tracing",
            "Use lazy formatting with `%s` placeholders instead of f-strings in log calls",
            "Configure log levels per environment: DEBUG for dev, WARNING for production",
            "Structure log output as JSON for machine-parseable log aggregation",
            "Never log sensitive data such as passwords, tokens, or PII",
        ],
    ),
    (
        "Test Patterns with pytest",
        "testing conventions using pytest, including fixture design, parametrization, and test organization patterns",
        [
            "Fixture Design and Scoping",
            "Parametrized Test Patterns",
            "Mock and Patch Strategies",
            "Integration Test Organization",
            "Test Data Factory Patterns",
            "Assertion Best Practices",
            "Async Test Conventions",
            "Coverage Configuration Standards",
            "Snapshot Testing Patterns",
            "Performance Test Conventions",
        ],
        [
            "Use descriptive test names following `test_<unit>_<scenario>_<expected>` pattern",
            "Prefer fixtures over setUp/tearDown for test resource management",
            "Use `pytest.mark.parametrize` to reduce test duplication",
            "Mock external dependencies at the boundary, not deep within the call stack",
            "Use factory functions or `factory_boy` for complex test data creation",
            "Keep test files mirroring the source directory structure",
            "Mark slow tests with `@pytest.mark.slow` for selective execution",
        ],
    ),
    (
        "Package Management Conventions",
        "Python package management using pyproject.toml, dependency specification, and virtual environment conventions",
        [
            "pyproject.toml Configuration Standards",
            "Dependency Specification Guidelines",
            "Virtual Environment Management",
            "Lock File Conventions",
            "Optional Dependency Groups",
            "Package Publishing Workflow",
            "Private Package Registry Setup",
            "Dependency Update Policies",
            "Build System Configuration",
            "Namespace Package Conventions",
        ],
        [
            "Use `pyproject.toml` as the single source of project metadata",
            "Pin direct dependencies to compatible release ranges using `~=` or `>=,<`",
            "Separate development dependencies into optional groups like `[dev]` and `[test]`",
            "Always commit lock files (e.g., `requirements.lock`) for reproducible builds",
            "Use a virtual environment for every project; never install into the system Python",
            "Define build system requirements in `[build-system]` table",
            "Run `pip audit` regularly to check for known vulnerabilities in dependencies",
        ],
    ),
    (
        "CI/CD Python Configuration",
        "continuous integration and deployment pipeline configuration for Python projects, including testing, linting, and release automation",
        [
            "GitHub Actions Workflow Design",
            "Matrix Testing Across Python Versions",
            "Linting and Formatting Pipeline",
            "Test Parallelization Strategies",
            "Artifact and Cache Management",
            "Release Automation Conventions",
            "Environment Variable Management in CI",
            "Docker Image Build Pipelines",
            "Security Scanning Integration",
            "Deployment Gate Conventions",
        ],
        [
            "Run linting, type checking, and tests as separate CI jobs for clear failure attribution",
            "Test against all supported Python versions using matrix builds",
            "Cache pip downloads and virtual environments to speed up CI runs",
            "Use `--fail-fast` in CI to abort early on critical failures",
            "Pin CI action versions to specific SHA hashes for security",
            "Separate CI workflows for pull requests and main branch pushes",
            "Store secrets in CI platform secret management, never in repository files",
        ],
    ),
    (
        "Advanced Type Hints",
        "advanced Python type annotation patterns using Protocol, TypeVar, Generic, and other typing constructs for expressive static analysis",
        [
            "Protocol Classes for Structural Typing",
            "TypeVar and Bounded Generics",
            "Generic Container Types",
            "Callable Type Annotations",
            "TypeGuard and Type Narrowing",
            "Literal and Final Types",
            "Overloaded Function Signatures",
            "ParamSpec for Decorator Typing",
            "TypeAlias and NewType Conventions",
            "Runtime Type Checking Patterns",
        ],
        [
            "Use `Protocol` for structural subtyping instead of abstract base classes where possible",
            "Define `TypeVar` with meaningful names that indicate the constraint (e.g., `UserT`, `ResponseT`)",
            "Prefer `Sequence` over `list` in function signatures for input parameters",
            "Use `TypeGuard` to help type checkers understand custom type narrowing functions",
            "Apply `@overload` to functions with different return types based on input types",
            "Use `Final` for constants that should not be reassigned",
            "Run `mypy --strict` in CI to catch type errors early",
        ],
    ),
    (
        "Import Organization",
        "Python import ordering, grouping, and style conventions using isort and manual best practices",
        [
            "Import Grouping and Ordering Rules",
            "Absolute vs Relative Import Conventions",
            "Circular Import Prevention",
            "Lazy Import Patterns",
            "Conditional Import Strategies",
            "Re-Export and Public API Definition",
            "Import Alias Conventions",
            "Star Import Prohibition",
            "Type-Checking-Only Imports",
            "isort Configuration Standards",
        ],
        [
            "Group imports in order: stdlib, third-party, local application, separated by blank lines",
            "Use absolute imports for all cross-package references",
            "Never use `from module import *` in production code",
            "Place `TYPE_CHECKING` imports inside `if TYPE_CHECKING:` blocks",
            "Use `__all__` to explicitly define the public API of a module",
            "Sort imports alphabetically within each group",
            "Configure isort with `profile = 'black'` for consistency with black formatting",
        ],
    ),
    (
        "Exception Handling Patterns",
        "Python exception handling conventions including custom exception hierarchies, error propagation, and recovery strategies",
        [
            "Custom Exception Hierarchy Design",
            "Exception Chaining Patterns",
            "Context Manager Error Handling",
            "Retry and Recovery Patterns",
            "Validation Error Aggregation",
            "Third-Party Exception Wrapping",
            "Logging in Exception Handlers",
            "Cleanup and Finally Block Conventions",
            "Exception Testing Strategies",
            "Async Exception Handling",
        ],
        [
            "Define a project-level base exception class that all custom exceptions inherit from",
            "Use `raise ... from ...` for exception chaining to preserve the original traceback",
            "Never use bare `except:` clauses; always specify the exception type",
            "Catch specific exceptions rather than broad `Exception` unless re-raising",
            "Include relevant context data in custom exception attributes",
            "Log exceptions at the handler level, not at the raise site",
            "Use `contextlib.suppress` for expected exceptions that need no handling",
        ],
    ),
    (
        "Dataclasses and attrs",
        "Python dataclass and attrs usage conventions for structured data modeling, immutability, and validation patterns",
        [
            "Dataclass Field Configuration",
            "Frozen Dataclass Patterns",
            "Post-Init Processing Conventions",
            "Attrs Validator Patterns",
            "Slot-Based Dataclass Optimization",
            "Dataclass Inheritance Guidelines",
            "Serialization and Deserialization",
            "Factory Function Patterns",
            "Comparison and Ordering Configuration",
            "Migration from NamedTuple to Dataclass",
        ],
        [
            "Use `frozen=True` for value objects that should be immutable after creation",
            "Define default values using `field(default_factory=...)` for mutable defaults",
            "Use `__post_init__` for derived field computation and validation",
            "Prefer `slots=True` for memory-efficient dataclasses in Python 3.10+",
            "Use attrs `@define` decorator for classes requiring complex validation",
            "Keep dataclass fields ordered: required fields first, then optional with defaults",
            "Use `asdict()` and `astuple()` for serialization rather than custom methods",
        ],
    ),
    (
        "Concurrent Processing",
        "Python concurrency patterns using threading, multiprocessing, and concurrent.futures for parallel task execution",
        [
            "ThreadPoolExecutor Patterns",
            "ProcessPoolExecutor for CPU-Bound Work",
            "Thread Safety and Locking Conventions",
            "Shared State Management",
            "Worker Pool Sizing Guidelines",
            "Future and Callback Patterns",
            "Graceful Shutdown Conventions",
            "Queue-Based Communication",
            "Concurrent Data Structure Usage",
            "Deadlock Prevention Strategies",
        ],
        [
            "Use `concurrent.futures` for high-level parallel execution instead of raw threads",
            "Choose `ThreadPoolExecutor` for I/O-bound and `ProcessPoolExecutor` for CPU-bound work",
            "Always use context managers (`with`) when creating executor instances",
            "Limit thread pool size to avoid resource exhaustion; default to `min(32, os.cpu_count() + 4)`",
            "Use `threading.Lock` to protect shared mutable state across threads",
            "Handle `KeyboardInterrupt` in concurrent code for clean shutdown",
            "Prefer immutable data when communicating between threads or processes",
        ],
    ),
    (
        "Security Best Practices",
        "Python application security conventions including input sanitization, secret management, and secure coding patterns",
        [
            "Input Validation and Sanitization",
            "Secret and Credential Management",
            "SQL Injection Prevention",
            "Cross-Site Scripting Prevention",
            "Cryptographic Operations Conventions",
            "Dependency Vulnerability Scanning",
            "Authentication Token Handling",
            "File Upload Security",
            "CORS Configuration Standards",
            "Secure Deserialization Patterns",
        ],
        [
            "Never trust user input; validate and sanitize all external data at the boundary",
            "Use parameterized queries exclusively; never interpolate user data into SQL strings",
            "Store secrets in environment variables or a secret manager, never in code or config files",
            "Use `secrets` module instead of `random` for security-sensitive token generation",
            "Apply the principle of least privilege for service accounts and API keys",
            "Run `pip audit` and `safety check` in CI to detect vulnerable dependencies",
            "Use `hashlib` with `pbkdf2_hmac` or `bcrypt` for password hashing, never MD5 or SHA1 alone",
        ],
    ),
    (
        "Performance Optimization",
        "Python performance optimization techniques including profiling, caching, algorithmic improvements, and memory management",
        [
            "Profiling and Benchmarking Conventions",
            "Caching Strategies with functools",
            "Generator-Based Memory Optimization",
            "Algorithm Complexity Guidelines",
            "String Operations Optimization",
            "Collection Type Selection",
            "Lazy Evaluation Patterns",
            "Database Query Optimization",
            "Serialization Performance",
            "Memory Profiling and Leak Detection",
        ],
        [
            "Profile before optimizing; use `cProfile` or `py-spy` to identify actual bottlenecks",
            "Use `functools.lru_cache` for expensive pure functions with hashable arguments",
            "Prefer generators over lists for large sequences that are consumed once",
            "Choose appropriate data structures: `set` for membership testing, `deque` for queue operations",
            "Use `str.join()` for concatenating many strings instead of repeated `+` operations",
            "Avoid premature optimization; focus on algorithmic complexity first",
            "Use `__slots__` on classes instantiated in large quantities to reduce memory overhead",
        ],
    ),
    (
        "Sphinx Documentation",
        "Python documentation generation using Sphinx, including docstring conventions, cross-referencing, and build configuration",
        [
            "Docstring Format Standards (Google Style)",
            "Sphinx Configuration Conventions",
            "Cross-Reference and Intersphinx Setup",
            "API Documentation Auto-Generation",
            "Narrative Documentation Structure",
            "Code Example Testing with doctest",
            "Extension and Plugin Usage",
            "Documentation Build Pipeline",
            "Versioned Documentation Patterns",
            "Changelog and Release Notes Conventions",
        ],
        [
            "Use Google-style docstrings consistently across all public APIs",
            "Include `Args`, `Returns`, and `Raises` sections in all function docstrings",
            "Configure intersphinx mapping for cross-project documentation links",
            "Run `sphinx-build -W` with warnings-as-errors in CI to catch broken references",
            "Use `autodoc` to generate API documentation from source code docstrings",
            "Test code examples in docstrings using `doctest` or `sphinx.ext.doctest`",
            "Keep narrative documentation (tutorials, guides) separate from API reference",
        ],
    ),
    (
        "Deployment Patterns",
        "Python application deployment conventions using Docker, WSGI/ASGI servers, and container orchestration patterns",
        [
            "Dockerfile Best Practices for Python",
            "WSGI Server Configuration (Gunicorn)",
            "ASGI Server Configuration (Uvicorn)",
            "Multi-Stage Docker Builds",
            "Health Check Endpoint Design",
            "Graceful Shutdown Implementation",
            "Environment-Based Configuration",
            "Container Resource Limits",
            "Log Forwarding in Containers",
            "Rolling Deployment Strategies",
        ],
        [
            "Use multi-stage Docker builds to minimize final image size",
            "Run Python applications as non-root users inside containers",
            "Set `--workers` based on CPU count: `2 * CPU + 1` for Gunicorn",
            "Implement `/health` and `/ready` endpoints for orchestrator probes",
            "Handle SIGTERM gracefully to allow in-flight requests to complete",
            "Use `.dockerignore` to exclude test files, docs, and development artifacts",
            "Pin base image versions to specific digests for reproducible builds",
        ],
    ),
    (
        "Configuration Management",
        "Python application configuration patterns using pydantic-settings, environment variables, and hierarchical config systems",
        [
            "pydantic-settings Configuration Classes",
            "Environment Variable Conventions",
            "Hierarchical Configuration Merging",
            "Secret Configuration Handling",
            "Feature Flag Patterns",
            "Per-Environment Configuration Files",
            "Configuration Validation on Startup",
            "Dynamic Configuration Reloading",
            "Default Value Conventions",
            "Configuration Documentation Generation",
        ],
        [
            "Use pydantic `BaseSettings` for type-safe configuration with environment variable support",
            "Prefix all application environment variables with a project-specific namespace",
            "Validate configuration eagerly at application startup, not at first use",
            "Separate secret configuration (credentials) from non-secret settings",
            "Provide sensible defaults for all non-secret configuration values",
            "Document all configuration options with `Field(description=...)`",
            "Use `.env` files for local development only; never commit them to version control",
        ],
    ),
    (
        "CLI Tool Development",
        "Python command-line interface development using click and typer, including argument parsing, output formatting, and user interaction",
        [
            "Command Group Organization",
            "Argument and Option Conventions",
            "Output Formatting Standards",
            "Progress Indicator Patterns",
            "Interactive Prompt Design",
            "Error Handling and Exit Codes",
            "Configuration File Integration",
            "Shell Completion Setup",
            "Plugin Architecture for CLIs",
            "CLI Testing Strategies",
        ],
        [
            "Use `typer` or `click` for CLI applications instead of raw `argparse`",
            "Group related subcommands under a common parent command",
            "Use `--verbose` / `--quiet` flags to control output verbosity",
            "Return appropriate exit codes: 0 for success, 1 for general errors, 2 for usage errors",
            "Use `rich` for formatted terminal output including tables and progress bars",
            "Support both interactive and non-interactive (piped) modes",
            "Provide `--output-format` option supporting `json`, `table`, and `text` formats",
        ],
    ),
    (
        "Data Processing Pipelines",
        "Python data processing patterns using pandas, pathlib, and standard library tools for ETL workflows and data transformation",
        [
            "DataFrame Operation Conventions",
            "File Path Handling with pathlib",
            "CSV and JSON Processing Patterns",
            "Data Validation and Cleaning",
            "Pipeline Composition Patterns",
            "Memory-Efficient Processing",
            "Error Recovery in Pipelines",
            "Logging and Monitoring for Pipelines",
            "Parallel Data Processing",
            "Output Format and Encoding Standards",
        ],
        [
            "Use `pathlib.Path` for all file path operations instead of `os.path`",
            "Prefer method chaining for pandas DataFrame transformations",
            "Process large files in chunks using `chunksize` parameter or generators",
            "Validate data schemas at pipeline entry points before processing",
            "Use `with` statements for all file operations to ensure proper resource cleanup",
            "Log pipeline progress at major stages with row counts and timing information",
            "Handle encoding explicitly; default to UTF-8 for all text file operations",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Code example templates (generic, parameterized by topic context)
# ---------------------------------------------------------------------------

def _to_snake(title: str) -> str:
    """Convert a title to snake_case identifier."""
    s = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    s = re.sub(r'\s+', '_', s.strip()).lower()
    return s[:30]


def _to_class(title: str) -> str:
    """Convert a title to PascalCase class name."""
    words = re.sub(r'[^a-zA-Z0-9\s]', '', title).split()
    return ''.join(w.capitalize() for w in words)[:30]


CODE_TEMPLATES = [
    # Template 0: Class with methods
    lambda topic, sub: f'''class {_to_class(sub)}Handler:
    """Handle {sub.lower()} operations.

    Implements the standard patterns for {topic.lower()}
    as defined in our project conventions.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._logger = logging.getLogger(__name__)

    def process(self, data: Any) -> dict[str, Any]:
        """Process data according to {sub.lower()} conventions.

        Args:
            data: Input data to process.

        Returns:
            Processed result dictionary.

        Raises:
            ValueError: If data is invalid.
        """
        self._validate(data)
        result = self._transform(data)
        self._logger.info("Processed %d items", len(result))
        return result

    def _validate(self, data: Any) -> None:
        """Validate input data."""
        if not data:
            raise ValueError("Input data must not be empty")

    def _transform(self, data: Any) -> dict[str, Any]:
        """Apply transformation logic."""
        return {{"status": "processed", "items": data}}''',

    # Template 1: Function with type hints
    lambda topic, sub: f'''def handle_{_to_snake(sub)}(
    input_data: list[dict[str, Any]],
    *,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Handle {sub.lower()} with standard conventions.

    Applies the project's {topic.lower()} guidelines
    to process the given input data safely.

    Args:
        input_data: List of data items to process.
        timeout: Maximum time in seconds for the operation.
        max_retries: Number of retry attempts on failure.

    Returns:
        Dictionary containing processed results and metadata.

    Raises:
        ValueError: If input_data is empty or malformed.
        TimeoutError: If processing exceeds the timeout.
    """
    if not input_data:
        raise ValueError("input_data must not be empty")

    logger = logging.getLogger(__name__)
    logger.info("Processing %d items for {_to_snake(sub)}", len(input_data))

    results = []
    for item in input_data:
        processed = _process_single_item(item)
        results.append(processed)

    return {{"count": len(results), "items": results}}''',

    # Template 2: Context manager pattern
    lambda topic, sub: f'''@contextmanager
def {_to_snake(sub)}_context(
    resource_id: str,
    options: dict[str, Any] | None = None,
) -> Generator[{_to_class(sub)}Session, None, None]:
    """Create a managed context for {sub.lower()}.

    Ensures proper resource acquisition and cleanup following
    the project's {topic.lower()} conventions.

    Args:
        resource_id: Identifier for the resource to manage.
        options: Optional configuration overrides.

    Yields:
        A configured session object.
    """
    options = options or {{}}
    logger = logging.getLogger(__name__)
    logger.debug("Acquiring {_to_snake(sub)} resource: %s", resource_id)

    session = {_to_class(sub)}Session(resource_id, **options)
    try:
        session.initialize()
        yield session
    except Exception:
        logger.exception("Error in {_to_snake(sub)} context")
        raise
    finally:
        session.cleanup()
        logger.debug("Released {_to_snake(sub)} resource: %s", resource_id)''',

    # Template 3: Async function
    lambda topic, sub: f'''async def {_to_snake(sub)}_async(
    items: list[str],
    concurrency: int = 10,
) -> list[dict[str, Any]]:
    """Process {sub.lower()} items asynchronously.

    Follows the project's {topic.lower()} conventions
    for async operations with controlled concurrency.

    Args:
        items: List of item identifiers to process.
        concurrency: Maximum number of concurrent operations.

    Returns:
        List of processed results.
    """
    semaphore = asyncio.Semaphore(concurrency)
    logger = logging.getLogger(__name__)

    async def _process_one(item: str) -> dict[str, Any]:
        async with semaphore:
            logger.debug("Processing item: %s", item)
            await asyncio.sleep(0)  # yield control
            return {{"id": item, "status": "completed"}}

    tasks = [_process_one(item) for item in items]
    results = await asyncio.gather(*tasks)
    logger.info("Completed %d items for {_to_snake(sub)}", len(results))
    return list(results)''',

    # Template 4: Dataclass + factory
    lambda topic, sub: f'''@dataclass(frozen=True, slots=True)
class {_to_class(sub)}Config:
    """Configuration for {sub.lower()}.

    Follows the project's {topic.lower()} conventions
    for immutable configuration objects.
    """
    name: str
    enabled: bool = True
    max_items: int = 100
    timeout_seconds: float = 30.0
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.max_items <= 0:
            raise ValueError("max_items must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @classmethod
    def from_env(cls, prefix: str = "{_to_snake(sub).upper()}") -> "{_to_class(sub)}Config":
        """Create configuration from environment variables.

        Args:
            prefix: Environment variable prefix.

        Returns:
            Configured instance.
        """
        import os
        return cls(
            name=os.environ.get(f"{{prefix}}_NAME", "default"),
            enabled=os.environ.get(f"{{prefix}}_ENABLED", "true").lower() == "true",
            max_items=int(os.environ.get(f"{{prefix}}_MAX_ITEMS", "100")),
            timeout_seconds=float(os.environ.get(f"{{prefix}}_TIMEOUT", "30.0")),
        )''',

    # Template 5: Decorator pattern
    lambda topic, sub: f'''def with_{_to_snake(sub)}(
    retries: int = 3,
    backoff_factor: float = 0.5,
) -> Callable[[F], F]:
    """Decorator to apply {sub.lower()} conventions.

    Wraps a function with retry logic and logging following
    the project's {topic.lower()} standards.

    Args:
        retries: Maximum number of retry attempts.
        backoff_factor: Multiplier for exponential backoff delay.

    Returns:
        Decorated function with retry behavior.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = logging.getLogger(func.__module__)
            last_exception: Exception | None = None
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    delay = backoff_factor * (2 ** (attempt - 1))
                    logger.warning(
                        "%s attempt %d/%d failed: %s (retry in %.1fs)",
                        func.__name__, attempt, retries, exc, delay,
                    )
                    time.sleep(delay)
            raise RuntimeError(
                f"{{func.__name__}} failed after {{retries}} attempts"
            ) from last_exception
        return wrapper  # type: ignore[return-value]
    return decorator''',
]


# ---------------------------------------------------------------------------
# Prose section generators
# ---------------------------------------------------------------------------

def _generate_introduction(topic_name: str, topic_desc: str, subtopic: str) -> str:
    """Generate an introduction section."""
    return textwrap.dedent(f"""\
    ## {topic_name}

    ### {subtopic}

    This section covers the conventions and best practices for {subtopic.lower()}
    within the broader context of {topic_desc}. Following these guidelines ensures
    consistency across the codebase and reduces the likelihood of common errors.

    Understanding {subtopic.lower()} is essential for maintaining high-quality Python
    code in our projects. The patterns described here have been refined through
    extensive use in production systems and reflect industry best practices adapted
    to our specific needs.
    """)


def _generate_guidelines_section(guidelines: list[str], subtopic: str) -> str:
    """Generate a guidelines section from bullet points."""
    lines = [f"#### Guidelines for {subtopic}\n"]
    lines.append(
        f"The following guidelines govern how {subtopic.lower()} should be "
        f"implemented and maintained in this project:\n"
    )
    for i, guideline in enumerate(guidelines, 1):
        lines.append(f"{i}. **Rule {i}**: {guideline}")
    lines.append("")
    return "\n".join(lines)


def _generate_code_section(topic_name: str, subtopic: str, variation: int) -> str:
    """Generate a code example section."""
    template_fn = CODE_TEMPLATES[variation % len(CODE_TEMPLATES)]
    code = template_fn(topic_name, subtopic)
    return textwrap.dedent(f"""\
    #### Code Example

    The following example demonstrates the recommended pattern for
    {subtopic.lower()}:

    ```python
    {code}
    ```

    **Explanation**: This example follows our project conventions by using
    explicit type annotations, comprehensive docstrings, and proper error
    handling. Note the use of logging instead of print statements, and the
    structured return types that facilitate downstream processing.
    """)


def _generate_best_practices(topic_name: str, subtopic: str, guidelines: list[str]) -> str:
    """Generate a best practices section."""
    lines = [f"#### Best Practices\n"]
    lines.append(
        f"When working with {subtopic.lower()} in the context of "
        f"{topic_name.lower()}, keep these practices in mind:\n"
    )
    for g in guidelines[:4]:
        lines.append(f"- {g}")
    lines.append("")
    lines.append(
        f"These practices help maintain code quality and reduce the risk of "
        f"introducing bugs or performance issues related to {subtopic.lower()}."
    )
    lines.append("")
    return "\n".join(lines)


def _generate_anti_patterns(topic_name: str, subtopic: str) -> str:
    """Generate an anti-patterns section."""
    return textwrap.dedent(f"""\
    #### Common Anti-Patterns

    Avoid the following anti-patterns when implementing {subtopic.lower()}:

    - **Ignoring error conditions**: Always handle potential failures explicitly
      rather than silently swallowing exceptions or returning None.
    - **Missing documentation**: Every public function and class must have a
      docstring explaining its purpose, parameters, and return value.
    - **Hardcoded configuration**: Extract configuration values into environment
      variables or configuration files rather than embedding them in code.
    - **Insufficient testing**: Write tests that cover both the happy path and
      edge cases, including error conditions and boundary values.

    These anti-patterns are commonly encountered during code reviews and should
    be addressed before merging any changes related to {topic_name.lower()}.
    """)


def _generate_additional_notes(topic_name: str, topic_desc: str, subtopic: str) -> str:
    """Generate additional notes to pad content."""
    return textwrap.dedent(f"""\
    #### Integration Notes

    When integrating {subtopic.lower()} into existing code, ensure that
    the surrounding code follows the same conventions described in this
    section. Consistency is more important than any individual rule, so
    when in doubt, follow the established patterns in the immediate
    codebase context.

    The conventions described here apply specifically to {topic_desc}.
    Other areas of the codebase may have different conventions that are
    documented in their respective sections.

    #### Compatibility Considerations

    These conventions are designed for Python 3.10 and later. When
    working with codebases that must support earlier Python versions,
    some syntax features (such as `match` statements, `|` union types,
    and `slots=True` on dataclasses) may need to be adapted. Consult
    the project's minimum Python version requirement before using
    version-specific features.

    For third-party library dependencies referenced in these conventions,
    always check compatibility with the project's pinned dependency
    versions before adopting new patterns.

    #### Review Checklist

    Before submitting code that involves {subtopic.lower()}, verify:

    - [ ] All public functions have complete docstrings with Args, Returns,
          and Raises sections
    - [ ] Type annotations are present on all function signatures
    - [ ] Error handling covers expected failure modes
    - [ ] Unit tests achieve adequate coverage of the new code
    - [ ] Logging follows the project's structured logging conventions
    - [ ] No sensitive data is exposed in logs or error messages

    This checklist should be used in conjunction with the project's
    general code review guidelines.
    """)


def _generate_references(topic_name: str) -> str:
    """Generate a references section."""
    return textwrap.dedent(f"""\
    #### References

    - Python official documentation: https://docs.python.org/3/
    - PEP 8 - Style Guide for Python Code
    - PEP 484 - Type Hints
    - PEP 585 - Type Hinting Generics in Standard Collections
    - Project internal wiki: {topic_name.lower().replace(' ', '-')} section

    ---
    """)


# ---------------------------------------------------------------------------
# Chunk generation
# ---------------------------------------------------------------------------

def generate_chunk(topic_idx: int, variation_idx: int) -> str:
    """Generate a single ~5KB chunk of Python convention content.

    Args:
        topic_idx: Index into TOPICS (0-19).
        variation_idx: Variation within topic (0-9).

    Returns:
        String content of approximately 5KB.
    """
    topic_name, topic_desc, subtopics, guidelines = TOPICS[topic_idx]
    subtopic = subtopics[variation_idx]

    parts = [
        _generate_introduction(topic_name, topic_desc, subtopic),
        _generate_guidelines_section(guidelines, subtopic),
        _generate_code_section(topic_name, subtopic, variation_idx),
        _generate_best_practices(topic_name, subtopic, guidelines),
        _generate_anti_patterns(topic_name, subtopic),
        _generate_additional_notes(topic_name, topic_desc, subtopic),
        _generate_references(topic_name),
    ]
    content = "\n".join(parts)

    # Pad or trim to reach target size range
    content = _adjust_size(content, topic_name, subtopic)
    return content


def _adjust_size(content: str, topic_name: str, subtopic: str) -> str:
    """Adjust content size to be within the target range (~5KB)."""
    current_size = len(content.encode("utf-8"))

    # If too short, add padding paragraphs
    padding_paragraphs = [
        (
            f"\nMaintaining consistency in {subtopic.lower()} across the project "
            f"requires ongoing attention during code reviews. Team members should "
            f"familiarize themselves with these conventions and apply them "
            f"consistently in all new code. Legacy code should be updated to "
            f"follow these conventions when it is modified for other reasons, "
            f"but bulk reformatting PRs should be avoided as they make git "
            f"blame less useful.\n"
        ),
        (
            f"\nThe conventions for {topic_name.lower()} described in this "
            f"section are enforced by automated tooling where possible. The CI "
            f"pipeline includes checks for style compliance, type correctness, "
            f"and test coverage. Pull requests that fail these checks will be "
            f"blocked from merging until the issues are resolved.\n"
        ),
        (
            f"\nPerformance implications should be considered when implementing "
            f"{subtopic.lower()}. While correctness and readability take priority "
            f"over raw performance in most cases, obvious performance pitfalls "
            f"such as unnecessary allocations, repeated database queries, or "
            f"synchronous I/O in async contexts should be avoided. When in "
            f"doubt, measure before optimizing.\n"
        ),
        (
            f"\nDocumentation for {subtopic.lower()} should be kept in sync "
            f"with the code. When conventions change, update this document "
            f"as part of the same pull request that modifies the code. "
            f"Outdated documentation is worse than no documentation, as it "
            f"leads to confusion and inconsistent implementations. Use "
            f"docstring tests where appropriate to ensure examples remain "
            f"accurate.\n"
        ),
        (
            f"\nNew team members should review this section on "
            f"{topic_name.lower()} as part of their onboarding process. "
            f"Understanding these conventions early prevents common mistakes "
            f"and reduces the number of review cycles needed for pull requests. "
            f"Pair programming with experienced team members is recommended "
            f"for the first few tasks involving {subtopic.lower()}.\n"
        ),
        (
            f"\nException handling in the context of {subtopic.lower()} "
            f"follows the general project conventions: catch specific "
            f"exceptions, log with context, and re-raise when the current "
            f"layer cannot meaningfully handle the error. Avoid suppressing "
            f"exceptions unless the failure is truly expected and benign. "
            f"Always include the original exception in the chain using "
            f"`raise ... from ...` syntax.\n"
        ),
        (
            f"\nType annotations are mandatory for all public functions "
            f"related to {subtopic.lower()}. Use the most specific type "
            f"available: prefer `Sequence[int]` over `Any` for input "
            f"parameters, and concrete types like `list[str]` for return "
            f"values. Generic types should be used when a function operates "
            f"on multiple types while maintaining type safety. Run mypy in "
            f"strict mode to verify annotation completeness.\n"
        ),
        (
            f"\nTesting conventions for {subtopic.lower()} require both "
            f"unit tests and integration tests. Unit tests should cover "
            f"individual functions in isolation using mocks for external "
            f"dependencies. Integration tests should verify that components "
            f"work together correctly with real (or realistic) dependencies. "
            f"Use pytest fixtures to share setup logic across related tests "
            f"and keep individual test functions focused on a single behavior.\n"
        ),
    ]

    idx = 0
    while current_size < TARGET_SIZE_MIN and idx < len(padding_paragraphs):
        content += padding_paragraphs[idx]
        current_size = len(content.encode("utf-8"))
        idx += 1

    # If still too short after all padding, add generic filler
    while current_size < TARGET_SIZE_MIN:
        content += (
            f"\nAdditional considerations for {topic_name.lower()} include "
            f"maintaining backward compatibility when updating shared libraries, "
            f"ensuring that all changes are covered by appropriate test cases, "
            f"and documenting any deviations from these conventions with clear "
            f"justification in the code review comments.\n"
        )
        current_size = len(content.encode("utf-8"))

    # If too long, trim from the end (keeping the closing reference line)
    if current_size > TARGET_SIZE_MAX:
        encoded = content.encode("utf-8")
        # Find the last complete line within the limit
        trimmed = encoded[:TARGET_SIZE_MAX].decode("utf-8", errors="ignore")
        last_newline = trimmed.rfind("\n")
        if last_newline > 0:
            content = trimmed[:last_newline] + "\n"

    return content


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate all 200 noise chunks."""
    NOISE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Noise Chunk Generator (Python Convention Content)")
    print("=" * 60)
    print(f"Output directory: {NOISE_DIR}")
    print(f"Topics: {len(TOPICS)}")
    print(f"Variations per topic: 10")
    print(f"Total chunks: {len(TOPICS) * 10}")
    print(f"Target size per chunk: {TARGET_SIZE_MIN}-{TARGET_SIZE_MAX} bytes")
    print()

    total_size = 0
    sizes = []

    for chunk_idx in range(len(TOPICS) * 10):
        topic_idx = chunk_idx // 10
        variation_idx = chunk_idx % 10

        content = generate_chunk(topic_idx, variation_idx)
        chunk_file = NOISE_DIR / f"chunk_{chunk_idx}.txt"
        chunk_file.write_text(content, encoding="utf-8")

        size = len(content.encode("utf-8"))
        total_size += size
        sizes.append(size)

        topic_name = TOPICS[topic_idx][0]
        subtopic = TOPICS[topic_idx][2][variation_idx]
        print(f"  chunk_{chunk_idx:03d}.txt: {size:,} bytes  [{topic_name} > {subtopic}]")

    print()
    print(f"Total chunks generated: {len(sizes)}")
    print(f"Total size: {total_size:,} bytes ({total_size / 1024:.1f} KB)")
    print(f"Average chunk size: {total_size / len(sizes):,.0f} bytes")
    print(f"Min chunk size: {min(sizes):,} bytes")
    print(f"Max chunk size: {max(sizes):,} bytes")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
