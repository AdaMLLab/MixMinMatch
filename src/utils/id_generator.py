"""Document ID generation using content hashing."""
import hashlib


def generate_id(text: str, length: int = 12) -> str:
    """
    Generate a short unique hash from text content.

    The hash is computed from normalized text (lowercased, whitespace normalized)
    to ensure identical content produces identical IDs regardless of formatting.

    Args:
        text: Document text content
        length: Length of returned hash (default 12 chars)

    Returns:
        Hex string of specified length (e.g., "a1b2c3d4e5f6")
    """
    # Normalize: lowercase and collapse whitespace
    normalized = ' '.join(text.lower().split())
    # MD5 hash and truncate
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()[:length]


__all__ = ["generate_id"]
