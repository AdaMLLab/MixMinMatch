"""Output schema definitions for all pipeline stages."""
import pyarrow as pa

# =============================================================================
# Standard Schema (per-source filtered/deduped data)
# =============================================================================
# Used for: filtered/, deduped/ outputs
# Columns: text, id (hash), source (single string)
STANDARD_SCHEMA = pa.schema([
    ("text", pa.string()),
    ("id", pa.string()),       # 12-char MD5 hash of normalized text
    ("source", pa.string()),   # e.g., "hplt2", "culturax", "c4"
])

# =============================================================================
# Consensus Schema (multi-source overlap)
# =============================================================================
# Used for: consensus/ outputs
# Columns: text, id (hash), source (list of strings)
CONSENSUS_SCHEMA = pa.schema([
    ("text", pa.string()),
    ("id", pa.string()),                    # 12-char MD5 hash
    ("source", pa.list_(pa.string())),      # e.g., ["c4", "culturax"]
])

__all__ = ["STANDARD_SCHEMA", "CONSENSUS_SCHEMA"]
