#!/usr/bin/env python3
"""
Standalone script for pairwise overlap analysis between data sources.

This script analyzes document overlap between pairs of data sources,
optionally counting tokens in the overlapping documents using the
Llama-3.2-3B tokenizer.

Run this AFTER filtering (or after MinHash dedup) to understand how much
content is shared between different data sources before/after deduplication.

Usage:
    # Analyze all pairs with token counting (default)
    python scripts/run_overlap_analysis.py --language tr

    # Analyze specific pairs only
    python scripts/run_overlap_analysis.py --language hi --pairs "fineweb2,culturax;hplt2,c4"

    # Analyze deduped data instead of filtered
    python scripts/run_overlap_analysis.py --language tr --stage deduped

    # Skip token counting for faster analysis
    python scripts/run_overlap_analysis.py --language tr --no-count-tokens

Output:
    Results are saved to data/{language}/overlap_analysis_{stage}.json
    and printed to console in a human-readable summary.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.dedup.overlap_analysis import main

if __name__ == "__main__":
    main()
