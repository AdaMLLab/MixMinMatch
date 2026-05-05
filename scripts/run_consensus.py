#!/usr/bin/env python3
"""
Build consensus subset from deduped data.

Finds documents appearing in 2+ sources and outputs them with the
CONSENSUS_SCHEMA: {'text', 'id', 'source'} where source is a list.

Methods:
    minhash - Uses minhash .dups artifacts to find near-duplicates (~80% Jaccard)
              across sources. This is the recommended method.
    hash    - Uses exact MD5 hashes to find identical documents. Legacy method
              that misses near-duplicates.

Usage:
    python scripts/run_consensus.py --language tr
    python scripts/run_consensus.py --language tr --method minhash
    python scripts/run_consensus.py --language hi --min-sources 3
    python scripts/run_consensus.py --language tr --method hash  # legacy
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.common import DATA_DIR, PARQUET_CONFIG
from src.dedup.consensus import build_consensus
from src.dedup.minhash_consensus import build_minhash_consensus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Build consensus subset from deduped data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Methods:
    minhash  Uses minhash .dups artifacts to find near-duplicates (~80% Jaccard
             similarity) across sources. Captures significantly more multi-source
             content than the hash method. Requires minhash stage to have been run.

    hash     Uses exact MD5 hashes to find identical documents across sources.
             This is the legacy method that misses near-duplicates. Use this
             for comparison or when minhash artifacts are not available.

Examples:
    # Build consensus using minhash method (recommended)
    python scripts/run_consensus.py --language tr

    # Build consensus using hash method (legacy)
    python scripts/run_consensus.py --language tr --method hash

    # Compare both methods
    python scripts/run_consensus.py --language tr --method hash --output data/tr/consensus_hash
    python scripts/run_consensus.py --language tr --method minhash --output data/tr/consensus_minhash
        """
    )
    parser.add_argument("--language", "-l", required=True, help="Language code (e.g., tr, hi, ar)")
    parser.add_argument("--method", "-M", choices=['minhash', 'hash'], default='minhash',
                       help="Consensus method: 'minhash' (near-duplicates, recommended) or 'hash' (exact MD5)")
    parser.add_argument("--min-sources", "-m", type=int, default=2,
                       help="Minimum number of sources for consensus (default: 2)")
    parser.add_argument("--max-files", type=int, default=PARQUET_CONFIG["max_files_per_subset"],
                       help=f"Maximum output files (default: {PARQUET_CONFIG['max_files_per_subset']})")
    parser.add_argument("--data-dir", "-d", type=str, default=None,
                       help="Base data directory (default: data/)")
    parser.add_argument("--output", "-o", type=str, default=None,
                       help="Output directory (default: data/{language}/consensus)")
    parser.add_argument("--input-dir", "-i", type=str, default=None,
                       help="Override filtered input directory (default: data/{language}/filtered)")

    args = parser.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else DATA_DIR
    output_dir = Path(args.output) if args.output else None
    input_dir = Path(args.input_dir) if args.input_dir else None

    logger.info(f"Building consensus subset for {args.language.upper()}")
    logger.info(f"Method: {args.method}")
    logger.info(f"Min sources: {args.min_sources}")
    logger.info(f"Max files: {args.max_files}")

    try:
        if args.method == 'minhash':
            output_dir = build_minhash_consensus(
                language=args.language,
                min_sources=args.min_sources,
                data_dir=data_dir,
                output_dir=output_dir,
                max_files=args.max_files,
                input_dir=input_dir,
            )
        else:
            output_dir = build_consensus(
                language=args.language,
                min_sources=args.min_sources,
                data_dir=data_dir,
                output_dir=output_dir,
                max_files=args.max_files,
            )
        logger.info(f"\nConsensus subset saved to: {output_dir}")
    except Exception as e:
        logger.error(f"Failed to build consensus: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
