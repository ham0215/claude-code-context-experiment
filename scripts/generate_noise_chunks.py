"""Generate noise chunks for context consumption experiments."""

import random
from pathlib import Path

# Technical topics for generating varied content
TOPICS = [
    ("Database Architecture", [
        "Normalization forms (1NF, 2NF, 3NF, BCNF)",
        "Index optimization strategies",
        "Query execution plans",
        "Transaction isolation levels",
        "ACID properties",
        "CAP theorem implications",
        "Sharding strategies",
        "Replication patterns",
    ]),
    ("Distributed Systems", [
        "Consensus algorithms (Paxos, Raft)",
        "Event sourcing patterns",
        "CQRS architecture",
        "Microservices communication",
        "Service mesh concepts",
        "Circuit breaker patterns",
        "Load balancing strategies",
        "Message queue systems",
    ]),
    ("Software Design Patterns", [
        "Creational patterns (Factory, Builder, Singleton)",
        "Structural patterns (Adapter, Decorator, Facade)",
        "Behavioral patterns (Observer, Strategy, Command)",
        "Repository pattern",
        "Unit of Work pattern",
        "Dependency injection",
        "Domain-driven design",
        "Clean architecture",
    ]),
    ("Network Protocols", [
        "TCP/IP stack layers",
        "HTTP/2 and HTTP/3 features",
        "WebSocket protocol",
        "TLS handshake process",
        "DNS resolution",
        "Load balancer algorithms",
        "CDN caching strategies",
        "API gateway patterns",
    ]),
    ("Cloud Computing", [
        "Infrastructure as Code",
        "Container orchestration",
        "Serverless architecture",
        "Auto-scaling strategies",
        "Multi-region deployment",
        "Disaster recovery planning",
        "Cost optimization",
        "Security best practices",
    ]),
    ("Machine Learning", [
        "Supervised learning algorithms",
        "Neural network architectures",
        "Feature engineering",
        "Model evaluation metrics",
        "Hyperparameter tuning",
        "Transfer learning",
        "Model deployment strategies",
        "MLOps practices",
    ]),
]

# Lorem ipsum variations for padding
LOREM_PARAGRAPHS = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
    "Curabitur pretium tincidunt lacus. Nulla gravida orci a odio. Nullam varius, turpis et commodo pharetra, est eros bibendum elit, nec luctus magna felis sollicitudin mauris.",
    "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.",
    "Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.",
    "Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem.",
    "At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident.",
    "Similique sunt in culpa qui officia deserunt mollitia animi, id est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio.",
]


def generate_technical_section(topic: str, subtopics: list[str]) -> str:
    """Generate a technical documentation section."""
    content = [f"# Technical Documentation: {topic}\n"]
    content.append(f"\n## Introduction to {topic}\n")
    content.append(
        f"{topic} is a critical aspect of modern software development. "
        f"Understanding these concepts is essential for building scalable, "
        f"maintainable, and efficient systems. This document covers key concepts "
        f"and best practices.\n"
    )

    for i, subtopic in enumerate(random.sample(subtopics, min(4, len(subtopics)))):
        content.append(f"\n### {subtopic}\n")
        content.append(
            f"{subtopic} represents an important consideration in {topic.lower()}. "
            f"When implementing solutions, developers must carefully evaluate "
            f"the trade-offs involved. Key factors include performance, "
            f"maintainability, and scalability requirements.\n"
        )

        # Add some bullet points
        content.append("\nKey considerations:\n")
        for j in range(random.randint(3, 5)):
            content.append(f"- Consideration {j+1}: Important aspect to evaluate\n")

        # Add a paragraph
        content.append(f"\n{random.choice(LOREM_PARAGRAPHS)}\n")

    return "".join(content)


def generate_code_example() -> str:
    """Generate a sample code block."""
    examples = [
        '''
```python
def example_function(data: list) -> dict:
    """Process data and return results."""
    results = {}
    for item in data:
        key = item.get("id")
        value = item.get("value", 0)
        results[key] = value * 2
    return results
```
''',
        '''
```python
class DataProcessor:
    """Process and transform data."""

    def __init__(self, config: dict):
        self.config = config
        self._cache = {}

    def process(self, input_data: list) -> list:
        return [self._transform(item) for item in input_data]

    def _transform(self, item: dict) -> dict:
        return {**item, "processed": True}
```
''',
        '''
```python
async def fetch_data(url: str) -> dict:
    """Fetch data from API endpoint."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```
''',
    ]
    return random.choice(examples)


def generate_chunk(chunk_id: int, target_size: int = 5000) -> str:
    """
    Generate a single noise chunk of approximately target_size characters.

    Args:
        chunk_id: Unique identifier for this chunk
        target_size: Target size in characters (default 5000 ~ 1250 tokens)

    Returns:
        Generated chunk content
    """
    topic, subtopics = random.choice(TOPICS)
    content = [generate_technical_section(topic, subtopics)]

    # Add code example occasionally
    if random.random() > 0.5:
        content.append("\n## Code Example\n")
        content.append(generate_code_example())

    # Pad with lorem ipsum to reach target size
    current_size = sum(len(c) for c in content)
    while current_size < target_size:
        content.append(f"\n{random.choice(LOREM_PARAGRAPHS)}\n")
        current_size = sum(len(c) for c in content)

    return "".join(content)


def generate_all_chunks(
    output_dir: Path,
    num_chunks: int = 1000,
    target_size: int = 5000,
) -> None:
    """
    Generate all noise chunks.

    Args:
        output_dir: Directory to save chunks
        num_chunks: Number of chunks to generate
        target_size: Target size per chunk in characters
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {num_chunks} noise chunks...")
    print(f"Target size per chunk: {target_size} characters (~{target_size//4} tokens)")
    print(f"Output directory: {output_dir}")
    print()

    for i in range(num_chunks):
        chunk_content = generate_chunk(i, target_size)
        chunk_file = output_dir / f"chunk_{i}.txt"
        chunk_file.write_text(chunk_content)

        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{num_chunks} chunks")

    print()
    print(f"Generated {num_chunks} chunks successfully!")

    # Calculate total size
    total_size = sum(f.stat().st_size for f in output_dir.glob("chunk_*.txt"))
    estimated_tokens = total_size // 4
    print(f"Total size: {total_size:,} bytes (~{estimated_tokens:,} tokens)")
    print(f"Estimated context coverage: {(estimated_tokens / 200_000) * 100:.1f}%")


def main():
    """Generate noise chunks for the experiment."""
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "noise_chunks"

    print("=" * 60)
    print("Noise Chunk Generator")
    print("=" * 60)
    print()

    # Check existing chunks
    if output_dir.exists():
        existing = list(output_dir.glob("chunk_*.txt"))
        if existing:
            print(f"Found {len(existing)} existing chunks in {output_dir}")
            response = input("Delete existing chunks and regenerate? (y/N): ").strip().lower()
            if response != "y":
                print("Keeping existing chunks.")
                return

            # Remove existing chunks
            for f in existing:
                f.unlink()
            print("Removed existing chunks.")
            print()

    # Generate chunks - enough for 100% context coverage
    # At ~1250 tokens per chunk, need ~160 chunks for 100% of 200K
    # Generate 200 to have buffer
    generate_all_chunks(output_dir, num_chunks=200, target_size=5000)


if __name__ == "__main__":
    main()
