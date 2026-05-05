"""Common configuration shared across all languages."""
import os
from pathlib import Path

# =============================================================================
# Paths
# =============================================================================
BASE_DIR = Path(__file__).parent.parent.parent  # Project root
DATA_DIR = BASE_DIR / "data"
DOWNLOADS_DIR = DATA_DIR / "downloads"
LOGS_DIR = DATA_DIR / "logs"

# =============================================================================
# CPU Core Management
# =============================================================================
# Always reserve 2 cores for system stability
NUM_WORKERS = max(1, os.cpu_count() - 2)

# =============================================================================
# MinHash Deduplication Configuration
# =============================================================================
# Language-agnostic, works for all languages
MINHASH_CONFIG = {
    "n_grams": 5,           # 5-gram shingles
    "num_buckets": 14,      # Number of LSH buckets
    "hashes_per_bucket": 8, # Hashes per bucket (total: 14 * 8 = 112 hashes)
    "similarity_threshold": 0.8,  # Jaccard similarity threshold
}

# =============================================================================
# Parquet File Configuration
# =============================================================================
# Constraints for HuggingFace datasets compatibility:
# - Max 200 files per subset
# - Page index for random access without loading entire row groups
# - Row group size ~128MB (scan size limit is 300MB)
PARQUET_CONFIG = {
    "max_files_per_subset": 200,
    "row_group_size": 128 * 1024 * 1024,  # 128MB
    "write_page_index": True,
    "compression": "zstd",
}

# =============================================================================
# Batch Processing Configuration
# =============================================================================
BATCH_SIZE = 20000  # Batch size for processing
