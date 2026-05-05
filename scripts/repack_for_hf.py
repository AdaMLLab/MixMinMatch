#!/usr/bin/env python3
"""
Repack parquet files for HuggingFace upload.

Requirements:
- Max file size: 300MB (300,000,000 bytes)
- Page index enabled for random access
- Smaller row-group sizes

Creates two subsets:
- minhash_deduped: All deduplicated data from all sources
- consensus: Documents appearing in 2+ sources
"""
import argparse
import logging
import shutil
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# HuggingFace requirements
MAX_FILE_SIZE = 280_000_000  # 280MB (conservative to stay under 300MB)
ROW_GROUP_SIZE = 10_000  # Smaller row groups for better random access
INITIAL_BATCH_SIZE = 50_000  # Initial estimate

# Standard output schema
OUTPUT_SCHEMA = pa.schema([
    pa.field("text", pa.string()),
    pa.field("id", pa.string()),
    pa.field("source", pa.string()),
])


def get_parquet_files(input_dir: Path) -> list[tuple[Path, str]]:
    """Get all parquet files from directory with source name."""
    files = []
    if input_dir.is_dir():
        # For deduped, files are organized by source subdirectory
        for subdir in sorted(input_dir.iterdir()):
            if subdir.is_dir():
                source_name = subdir.name
                for f in sorted(subdir.glob("*.parquet")):
                    if f.stat().st_size > 0:
                        files.append((f, source_name))
        # Also check for files directly in the directory (for consensus)
        for f in sorted(input_dir.glob("*.parquet")):
            if f.stat().st_size > 0:
                files.append((f, "consensus"))
    return files


def normalize_batch(batch: pa.RecordBatch, source: str) -> pa.Table:
    """Normalize batch to output schema."""
    text_col = batch.column("text")
    id_col = batch.column("id")

    # Check if source is already a column (for consensus data)
    if "source" in batch.schema.names:
        source_col = batch.column("source")
        # Convert list to string if needed
        if pa.types.is_list(source_col.type):
            source_col = pa.array([",".join(s.as_py()) if s.as_py() else source
                                   for s in source_col], type=pa.string())
    else:
        # Create source column
        source_col = pa.array([source] * len(batch), type=pa.string())

    return pa.Table.from_arrays(
        [text_col, id_col, source_col],
        schema=OUTPUT_SCHEMA
    )


def write_parquet_file(table: pa.Table, output_path: Path) -> int:
    """Write parquet file with HF-compatible settings. Returns file size."""
    pq.write_table(
        table,
        output_path,
        row_group_size=ROW_GROUP_SIZE,
        write_page_index=True,
        compression='zstd',
        compression_level=3,
    )
    return output_path.stat().st_size


def repack_parquet_files(
    input_dir: Path,
    output_dir: Path,
    subset_name: str,
    max_file_size: int = MAX_FILE_SIZE,
):
    """Repack parquet files with HuggingFace-compatible settings."""
    # Clean and create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_files = get_parquet_files(input_dir)
    if not input_files:
        logger.error(f"No parquet files found in {input_dir}")
        return

    logger.info(f"Found {len(input_files)} input files")
    logger.info(f"Output schema: {OUTPUT_SCHEMA}")

    file_idx = 0
    current_tables = []
    current_rows = 0
    total_rows = 0

    # Dynamic batch size adjustment
    target_rows = INITIAL_BATCH_SIZE
    bytes_per_row_estimate = None

    for input_file, source in input_files:
        logger.info(f"Processing {input_file.parent.name}/{input_file.name} (source: {source})...")

        parquet_file = pq.ParquetFile(input_file)

        for batch in parquet_file.iter_batches(batch_size=10_000):
            # Normalize to output schema
            table = normalize_batch(batch, source)
            batch_rows = len(batch)
            current_tables.append(table)
            current_rows += batch_rows
            total_rows += batch_rows

            # Check if we should write a file
            if current_rows >= target_rows:
                combined = pa.concat_tables(current_tables)

                # Write to temp file first to check size
                temp_path = output_dir / f"temp_{file_idx:05d}.parquet"
                file_size = write_parquet_file(combined, temp_path)

                # Update bytes per row estimate
                bytes_per_row_estimate = file_size / len(combined)

                if file_size <= max_file_size:
                    # File is good, rename it
                    final_path = output_dir / f"{file_idx:05d}.parquet"
                    temp_path.rename(final_path)
                    logger.info(f"Wrote {final_path.name}: {len(combined):,} rows, {file_size/1e6:.1f}MB")
                    file_idx += 1
                    current_tables = []
                    current_rows = 0

                    # Adjust target rows for next file
                    target_rows = int(max_file_size / bytes_per_row_estimate * 0.9)
                    target_rows = max(10_000, min(target_rows, 500_000))
                else:
                    # File too large, need to split
                    temp_path.unlink()  # Remove temp file

                    # Calculate how many rows we can fit
                    safe_rows = int(len(combined) * max_file_size / file_size * 0.85)
                    safe_rows = max(10_000, safe_rows)

                    logger.info(f"File too large ({file_size/1e6:.1f}MB), splitting at {safe_rows:,} rows")

                    # Split and write first part
                    first_part = combined.slice(0, safe_rows)
                    final_path = output_dir / f"{file_idx:05d}.parquet"
                    first_size = write_parquet_file(first_part, final_path)
                    logger.info(f"Wrote {final_path.name}: {len(first_part):,} rows, {first_size/1e6:.1f}MB")
                    file_idx += 1

                    # Keep remainder for next iteration
                    remainder = combined.slice(safe_rows)
                    current_tables = [remainder]
                    current_rows = len(remainder)

                    # Update target
                    target_rows = safe_rows

    # Write remaining rows
    if current_tables:
        combined = pa.concat_tables(current_tables)
        if len(combined) > 0:
            output_path = output_dir / f"{file_idx:05d}.parquet"
            file_size = write_parquet_file(combined, output_path)

            if file_size > max_file_size:
                # Need to split final file too
                output_path.unlink()
                safe_rows = int(len(combined) * max_file_size / file_size * 0.85)

                offset = 0
                while offset < len(combined):
                    chunk_end = min(offset + safe_rows, len(combined))
                    chunk = combined.slice(offset, chunk_end - offset)

                    final_path = output_dir / f"{file_idx:05d}.parquet"
                    chunk_size = write_parquet_file(chunk, final_path)
                    logger.info(f"Wrote {final_path.name}: {len(chunk):,} rows, {chunk_size/1e6:.1f}MB")

                    file_idx += 1
                    offset = chunk_end
            else:
                logger.info(f"Wrote {output_path.name}: {len(combined):,} rows, {file_size/1e6:.1f}MB")
                file_idx += 1

    logger.info(f"Completed {subset_name}: {file_idx} files, {total_rows:,} total rows")


def main():
    parser = argparse.ArgumentParser(description="Repack parquet files for HuggingFace")
    parser.add_argument("--language", "-l", required=True, help="Language code (e.g., th)")
    parser.add_argument("--data-dir", "-d", type=str, default="data", help="Base data directory")
    parser.add_argument("--subset", "-s", choices=["minhash_deduped", "consensus", "both"],
                       default="both", help="Which subset to process")

    args = parser.parse_args()

    data_dir = Path(args.data_dir) / args.language

    if args.subset in ["minhash_deduped", "both"]:
        logger.info("=" * 60)
        logger.info("Processing minhash_deduped subset...")
        logger.info("=" * 60)

        input_dir = data_dir / "deduped"
        output_dir = data_dir / "hf_upload" / "minhash_deduped"

        repack_parquet_files(input_dir, output_dir, "minhash_deduped")

    if args.subset in ["consensus", "both"]:
        logger.info("=" * 60)
        logger.info("Processing consensus subset...")
        logger.info("=" * 60)

        input_dir = data_dir / "consensus"
        output_dir = data_dir / "hf_upload" / "consensus"

        repack_parquet_files(input_dir, output_dir, "consensus")

    logger.info("Done!")


if __name__ == "__main__":
    main()
