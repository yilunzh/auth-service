"""Breached password checking via a Bloom filter.

Loads a list of common breached passwords into a pure-Python Bloom filter
at startup. Passwords are checked case-insensitively.

Fails open: if the filter isn't initialized, ``is_breached`` returns False
so that the service doesn't block legitimate registrations.
"""

from __future__ import annotations

import hashlib
import logging
import math
from pathlib import Path

logger = logging.getLogger(__name__)

# Bloom filter state
_bit_array: bytearray | None = None
_num_bits: int = 0
_num_hashes: int = 0

# Default data file location
_DEFAULT_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "breached_passwords.txt"


def _optimal_params(n: int, fp_rate: float = 0.001) -> tuple[int, int]:
    """Calculate optimal Bloom filter size and hash count.

    Args:
        n: Expected number of items.
        fp_rate: Desired false positive rate.

    Returns:
        (num_bits, num_hashes)
    """
    m = int(-n * math.log(fp_rate) / (math.log(2) ** 2))
    k = max(1, int((m / n) * math.log(2)))
    return m, k


def _get_bit_positions(item: str, num_bits: int, num_hashes: int) -> list[int]:
    """Compute bit positions using double hashing (SHA-256 + MD5)."""
    h1 = int(hashlib.sha256(item.encode("utf-8")).hexdigest(), 16)
    h2 = int(hashlib.md5(item.encode("utf-8")).hexdigest(), 16)  # nosec B324
    return [(h1 + i * h2) % num_bits for i in range(num_hashes)]


def init_bloom_filter(data_path: str | Path | None = None) -> int:
    """Initialize the Bloom filter from a breached passwords file.

    Each line in the file is treated as one password (case-insensitive).
    Returns the number of passwords loaded.

    Idempotent: subsequent calls are no-ops if already initialized.
    """
    global _bit_array, _num_bits, _num_hashes

    if _bit_array is not None:
        return 0  # Already initialized

    path = Path(data_path) if data_path else _DEFAULT_DATA_PATH
    if not path.exists():
        logger.warning("Breached password file not found at %s — skipping", path)
        return 0

    # Read passwords
    passwords = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            pw = line.strip()
            if pw:
                passwords.append(pw.lower())

    if not passwords:
        logger.warning("Breached password file is empty — skipping")
        return 0

    # Initialize filter
    _num_bits, _num_hashes = _optimal_params(len(passwords))
    _bit_array = bytearray((_num_bits + 7) // 8)

    # Insert all passwords
    for pw in passwords:
        for pos in _get_bit_positions(pw, _num_bits, _num_hashes):
            _bit_array[pos // 8] |= 1 << (pos % 8)

    logger.info(
        "Bloom filter initialized: %d passwords, %d bits, %d hashes",
        len(passwords),
        _num_bits,
        _num_hashes,
    )
    return len(passwords)


def is_breached(password: str) -> bool:
    """Check if a password appears in the breached password list.

    Case-insensitive. Returns False (fail-open) if the filter is not initialized.
    """
    if _bit_array is None:
        return False

    normalized = password.lower()
    for pos in _get_bit_positions(normalized, _num_bits, _num_hashes):
        if not (_bit_array[pos // 8] & (1 << (pos % 8))):
            return False
    return True


def reset():
    """Reset the Bloom filter state (for testing)."""
    global _bit_array, _num_bits, _num_hashes
    _bit_array = None
    _num_bits = 0
    _num_hashes = 0
