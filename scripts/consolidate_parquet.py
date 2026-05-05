#!/usr/bin/env python3
"""
Consolidate parquet files to stay within HuggingFace limits.

Merges many small parquet files into fewer larger ones while:
- Maintaining max 200 files per subset
- Using proper row group sizes (~128MB)
- Enabling page index for random access
- Enforcing the standard schema

Usage:
    # Consolidate a specific directory
    python scripts/consolidate_parquet.py --input data/tr/deduped/hplt2 --output data/tr/deduped_consolidated/hplt2

    # Consolidate all sources for a language/stage
    python scripts/consolidate_parquet.py --language tr --stage deduped

    # Custom max files limit
    python scripts/consolidate_parquet.py --input data/tr/filtered/culturax --max-files 100
"""
import argparse
import logging
import math
import sys
from pathlib import Path
from typing import Optional

import pyarrow as pa
import pyarrow.parquet as pq

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.common import DATA_DIR, PARQUET_CONFIG, NUM_WORKERS
from src.config.schema import STANDARD_SCHEMA

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_file_row_count(parquet_path: Path) -> int:
    """Get row count from parquet file without loading data."""
    try:
        metadata = pq.read_metadata(parquet_path)
        return metadata.num_rows
    except Exception:
        return 0


def consolidate_directory(
    input_dir: Path,
    output_dir: Path,
    max_files: int = 200,
    target_schema: Optional[pa.Schema] = None,
) -> int:
    """
    Consolidate parquet files from input_dir to output_dir.

    Args:
        input_dir: Directory containing parquet files to consolidate
        output_dir: Output directory for consolidated files
        max_files: Maximum number of output files
        target_schema: Schema to use for output (default: STANDARD_SCHEMA)

    Returns:
        Number of documents written
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # Find all parquet files
    input_files = sorted(input_dir.glob("**/*.parquet"))
    if not input_files:
        logger.warning(f"No parquet files found in {input_dir}")
        return 0

    logger.info(f"Found {len(input_files)} input files")

    # If already within limit, just copy with proper settings
    if len(input_files) <= max_files:
        logger.info(f"Already within {max_files} file limit, rewriting with proper settings...")

    # Calculate total rows to determine batching
    total_rows = sum(get_file_row_count(f) for f in input_files)
    logger.info(f"Total rows: {total_rows:,}")

    if total_rows == 0:
        logger.warning("No data to consolidate")
        return 0

    # Calculate rows per output file
    rows_per_file = math.ceil(total_rows / max_files)
    logger.info(f"Target rows per file: ~{rows_per_file:,}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Read and write in batches
    target_schema = target_schema or STANDARD_SCHEMA
    current_batch = []
    current_rows = 0
    file_idx = 0
    total_written = 0

    for input_file in input_files:
        try:
            table = pq.read_table(input_file)

            # Convert to target schema if needed
            if table.schema != target_schema:
                # Extract only columns in target schema
                columns = {}
                for field in target_schema:
                    if field.name in table.column_names:
                        columns[field.name] = table[field.name]
                    else:
                        # Create empty column if missing
                        columns[field.name] = pa.nulls(table.num_rows, type=field.type)
                table = pa.table(columns, schema=target_schema)

            current_batch.append(table)
            current_rows += table.num_rows

            # Write when batch is full
            if current_rows >= rows_per_file:
                combined = pa.concat_tables(current_batch)
                output_path = output_dir / f"{file_idx:05d}.parquet"

                pq.write_table(
                    combined,
                    output_path,
                    row_group_size=PARQUET_CONFIG["row_group_size"],
                    write_page_index=PARQUET_CONFIG["write_page_index"],
                    compression=PARQUET_CONFIG["compression"],
                )

                logger.info(f"Wrote {combined.num_rows:,} rows to {output_path.name}")
                total_written += combined.num_rows

                current_batch = []
                current_rows = 0
                file_idx += 1

        except Exception as e:
            logger.warning(f"Error processing {input_file}: {e}")
            continue

    # Write remaining batch
    if current_batch:
        combined = pa.concat_tables(current_batch)
        output_path = output_dir / f"{file_idx:05d}.parquet"

        pq.write_table(
            combined,
            output_path,
            row_group_size=PARQUET_CONFIG["row_group_size"],
            write_page_index=PARQUET_CONFIG["write_page_index"],
            compression=PARQUET_CONFIG["compression"],
        )

        logger.info(f"Wrote {combined.num_rows:,} rows to {output_path.name}")
        total_written += combined.num_rows
        file_idx += 1

    logger.info(f"\nConsolidation complete:")
    logger.info(f"  Input files: {len(input_files)}")
    logger.info(f"  Output files: {file_idx}")
    logger.info(f"  Total rows: {total_written:,}")

    return total_written


def main():
    parser = argparse.ArgumentParser(description="Consolidate parquet files")
    parser.add_argument("--input", "-i", type=str, help="Input directory")
    parser.add_argument("--output", "-o", type=str, help="Output directory")
    parser.add_argument("--language", "-l", help="Language code for batch processing")
    parser.add_argument("--stage", "-s", help="Stage to consolidate (filtered, deduped)")
    parser.add_argument("--max-files", type=int, default=PARQUET_CONFIG["max_files_per_subset"],
                       help=f"Maximum output files (default: {PARQUET_CONFIG['max_files_per_subset']})")
    parser.add_argument("--in-place", action="store_true",
                       help="Replace input with consolidated output")

    args = parser.parse_args()

    if args.input:
        # Single directory mode
        input_dir = Path(args.input)
        if args.output:
            output_dir = Path(args.output)
        elif args.in_place:
            # Write to temp, then replace
            output_dir = input_dir.parent / f"{input_dir.name}_consolidated"
        else:
            parser.error("Must provide --output or --in-place")
            return

        consolidate_directory(input_dir, output_dir, max_files=args.max_files)

        if args.in_place:
            import shutil
            logger.info(f"Replacing {input_dir} with consolidated version...")
            backup_dir = input_dir.parent / f"{input_dir.name}_backup"
            shutil.move(str(input_dir), str(backup_dir))
            shutil.move(str(output_dir), str(input_dir))
            shutil.rmtree(str(backup_dir))
            logger.info("In-place consolidation complete")

    elif args.language and args.stage:
        # Batch mode - process all sources
        stage_dir = DATA_DIR / args.language / args.stage
        if not stage_dir.exists():
            logger.error(f"Stage directory not found: {stage_dir}")
            sys.exit(1)

        source_dirs = [d for d in stage_dir.iterdir() if d.is_dir() and d.name != "misc"]
        logger.info(f"Found {len(source_dirs)} sources to consolidate")

        for source_dir in sorted(source_dirs):
            logger.info(f"\n{'=' * 50}")
            logger.info(f"Consolidating {source_dir.name}...")
            logger.info("=" * 50)

            output_dir = stage_dir / f"{source_dir.name}_consolidated"
            consolidate_directory(source_dir, output_dir, max_files=args.max_files)

            if args.in_place:
                import shutil
                backup_dir = stage_dir / f"{source_dir.name}_backup"
                shutil.move(str(source_dir), str(backup_dir))
                shutil.move(str(output_dir), str(source_dir))
                shutil.rmtree(str(backup_dir))

    else:
        parser.error("Must provide --input OR --language with --stage")


if __name__ == "__main__":
    main()
