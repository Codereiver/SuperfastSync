"""Synthetic file generation for download benchmarking."""

import io
from typing import Iterator, Optional


class SyntheticFile:
    """Definition of a synthetic test file."""

    def __init__(self, name: str, size_bytes: int, description: str = ""):
        self.name = name
        self.size_bytes = size_bytes
        self.description = description

    def __repr__(self):
        return f"SyntheticFile({self.name}, {self.size_bytes} bytes)"


# Predefined synthetic test files
SYNTHETIC_FILES = [
    SyntheticFile(
        name="test-100mb.bin",
        size_bytes=100 * 1024 * 1024,  # 100 MB
        description="100 MB test file for download benchmarking"
    ),
    SyntheticFile(
        name="test-500mb.bin",
        size_bytes=500 * 1024 * 1024,  # 500 MB
        description="500 MB test file for download benchmarking"
    ),
    SyntheticFile(
        name="test-1gb.bin",
        size_bytes=1024 * 1024 * 1024,  # 1 GB
        description="1 GB test file for download benchmarking"
    ),
]

# Create a lookup dictionary for quick access
SYNTHETIC_FILES_MAP = {sf.name: sf for sf in SYNTHETIC_FILES}


def is_synthetic_file(filename: str) -> bool:
    """Check if a filename is a synthetic file."""
    return filename in SYNTHETIC_FILES_MAP


def get_synthetic_file(filename: str) -> Optional[SyntheticFile]:
    """Get a synthetic file definition by name."""
    return SYNTHETIC_FILES_MAP.get(filename)


def generate_synthetic_data(size_bytes: int, chunk_size: int = 64 * 1024) -> Iterator[bytes]:
    """
    Generate synthetic binary data in chunks.

    Uses a repeating pattern of bytes to generate data efficiently without
    consuming memory proportional to the file size.

    Args:
        size_bytes: Total size of data to generate
        chunk_size: Size of each chunk (default 64KB)

    Yields:
        Chunks of binary data
    """
    # Create a repeating pattern (8KB of data that repeats)
    pattern_size = 8 * 1024
    pattern = bytes(i % 256 for i in range(pattern_size))

    remaining = size_bytes
    while remaining > 0:
        # Determine chunk size for this iteration
        current_chunk_size = min(chunk_size, remaining)

        # Yield the pattern repeated to fill the chunk
        chunk = b""
        chunk_remaining = current_chunk_size
        while chunk_remaining > 0:
            chunk_part = pattern[:min(pattern_size, chunk_remaining)]
            chunk += chunk_part
            chunk_remaining -= len(chunk_part)

        yield chunk
        remaining -= current_chunk_size


def create_synthetic_file_stream(filename: str) -> Optional[Iterator[bytes]]:
    """
    Create a streaming generator for a synthetic file.

    Args:
        filename: Name of the synthetic file

    Returns:
        Generator yielding file data, or None if not a synthetic file
    """
    synthetic_file = get_synthetic_file(filename)
    if not synthetic_file:
        return None

    return generate_synthetic_data(synthetic_file.size_bytes)
