"""
Generates deterministic multicultural avatars using Multiavatar.

Given the same seed (e.g. a user ID), the output is always identical.
"""

from multiavatar.multiavatar import multiavatar


def generate(seed: str) -> str:
    """
    Generate a deterministic SVG avatar for the given seed.

    Args:
        seed: Deterministic seed (typically the user's ID as a string).

    Returns:
        SVG markup as a string.
    """
    return multiavatar(seed, None, None)
