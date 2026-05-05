#!/usr/bin/env python3
"""
Token counting utility script.

Counts tokens in parquet files using the Llama-3.2-3B tokenizer.
Results are logged to data/token_stats.json.

Usage:
    # Count tokens for a specific stage and source
    python scripts/run_token_count.py --language tr --stage filtered --source hplt2

    # Count tokens for all sources at a stage
    python scripts/run_token_count.py --language tr --stage filtered

    # Count tokens for a specific directory
    python scripts/run_token_count.py --directory data/tr/deduped/culturax

    # Print summary of all logged token stats
    python scripts/run_token_count.py --summary
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.common import DATA_DIR, NUM_WORKERS
from src.tokenization import TokenCounter, TokenStatsLogger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Count tokens in parquet files")
    parser.add_argument("--language", "-l", help="Language code (e.g., tr, hi, ar)")
    parser.add_argument("--stage", "-s", help="Pipeline stage (download, filtered, deduped, consensus)")
    parser.add_argument("--source", help="Source name (e.g., hplt2, culturax)")
    parser.add_argument("--directory", "-d", help="Direct directory path to count")
    parser.add_argument("--summary", action="store_true", help="Print summary of logged stats")
    parser.add_argument("--workers", "-w", type=int, default=NUM_WORKERS, help="Number of parallel workers")

    args = parser.parse_args()

    stats_logger = TokenStatsLogger(DATA_DIR / "token_stats.json")

    if args.summary:
        stats_logger.print_summary(args.language)
        return

    # Determine directory to count
    if args.directory:
        target_dir = Path(args.directory)
        language = args.language or "unknown"
        stage = args.stage or "unknown"
        source = args.source or target_dir.name
    elif args.language and args.stage:
        if args.source:
            target_dir = DATA_DIR / args.language / args.stage / args.source
            source = args.source
        else:
            # Count all sources at this stage
            stage_dir = DATA_DIR / args.language / args.stage
            if not stage_dir.exists():
                logger.error(f"Stage directory not found: {stage_dir}")
                sys.exit(1)

            source_dirs = [d for d in stage_dir.iterdir() if d.is_dir() and d.name != "misc"]
            if not source_dirs:
                logger.error(f"No source directories found in {stage_dir}")
                sys.exit(1)

            logger.info(f"Found {len(source_dirs)} sources: {[d.name for d in source_dirs]}")

            counter = TokenCounter()
            for source_dir in sorted(source_dirs):
                logger.info(f"\nCounting tokens for {source_dir.name}...")
                stats = counter.count_directory(source_dir, num_workers=args.workers)
                stats_logger.log_stage(args.language, args.stage, source_dir.name, stats)

            stats_logger.print_summary(args.language)
            return

        language = args.language
        stage = args.stage
    else:
        parser.error("Must provide --directory OR --language with --stage")
        return

    if not target_dir.exists():
        logger.error(f"Directory not found: {target_dir}")
        sys.exit(1)

    logger.info(f"Counting tokens in: {target_dir}")
    logger.info(f"Using {args.workers} workers")

    counter = TokenCounter()
    stats = counter.count_directory(target_dir, num_workers=args.workers)

    logger.info(f"\nResults:")
    logger.info(f"  Total documents: {stats['total_docs']:,}")
    logger.info(f"  Total tokens: {stats['total_tokens']:,}")

    # Log to stats file
    stats_logger.log_stage(language, stage, source, stats)
    logger.info(f"\nStats logged to: {stats_logger.log_path}")


if __name__ == "__main__":
    main()
