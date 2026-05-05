#!/usr/bin/env python3
"""
Unified Pipeline Runner for Multi-Language Pretraining Data.

This script provides a unified CLI interface for running the data pipeline
for Arabic, Turkish, and Hindi languages.

Usage:
    python run_pipeline.py --language tr --stage download
    python run_pipeline.py --language tr --stage filter
    python run_pipeline.py --language tr --stage minhash
    python run_pipeline.py --language hi --stage all

Stages:
    download  - Download datasets from HuggingFace
    filter    - Apply quality filtering
    minhash   - Run MinHash deduplication
    all       - Run all stages sequentially
"""
import argparse
import logging
import os
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import configurations
from src.config.common import DATA_DIR, MINHASH_CONFIG, NUM_WORKERS
from src.config import DATASETS, FILTER_CONFIGS

# Import filters
from src.filters import ArabicQualityFilter
from src.filters.tr_quality import TrQualityFilter
from src.filters.hi_quality import HiQualityFilter
from src.filters.it_quality import ItQualityFilter
from src.filters.th_quality import ThQualityFilter

# Import download utilities
from src.download import (
    download_arabic_datasets,
    download_turkish_datasets,
    download_hindi_datasets,
    download_italian_datasets,
    download_thai_datasets,
)

# Import deduplication utilities
from src.dedup import (
    MinhashDedupSignature,
    MinhashDedupBuckets,
    MinhashDedupCluster,
    MinhashDedupFilter,
)


# Filter class mapping
FILTER_CLASSES = {
    "ar": ArabicQualityFilter,
    "tr": TrQualityFilter,
    "hi": HiQualityFilter,
    "it": ItQualityFilter,
    "th": ThQualityFilter,
}

# Download function mapping
DOWNLOAD_FUNCTIONS = {
    "ar": download_arabic_datasets,
    "tr": download_turkish_datasets,
    "hi": download_hindi_datasets,
    "it": download_italian_datasets,
    "th": download_thai_datasets,
}


def get_data_dir(language: str) -> Path:
    """Get the data directory for a language."""
    return DATA_DIR / language


def run_download(language: str, dry_run: bool = False) -> bool:
    """
    Run the download stage for a language.

    Args:
        language: Language code (ar, tr, hi)
        dry_run: If True, only print commands without executing

    Returns:
        True if successful
    """
    logger.info(f"Starting download stage for {language.upper()}")

    download_func = DOWNLOAD_FUNCTIONS.get(language)
    if download_func is None:
        logger.error(f"Unknown language: {language}")
        return False

    return download_func(dry_run=dry_run)


def run_filter(
    language: str,
    input_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    limit: Optional[int] = None,
) -> bool:
    """
    Run the quality filtering stage for a language.

    Args:
        language: Language code (ar, tr, hi)
        input_dir: Input directory (default: data/{lang}/downloads)
        output_dir: Output directory (default: data/{lang}/filtered)
        limit: Limit number of documents to process (for testing)

    Returns:
        True if successful
    """
    from datatrove.executor import LocalPipelineExecutor
    from datatrove.pipeline.readers import ParquetReader
    from datatrove.pipeline.writers import ParquetWriter

    logger.info(f"Starting filter stage for {language.upper()}")

    # Get filter class and config
    filter_class = FILTER_CLASSES.get(language)
    filter_config = FILTER_CONFIGS.get(language)

    if filter_class is None:
        logger.error(f"Unknown language: {language}")
        return False

    # Set up directories
    data_dir = get_data_dir(language)
    input_dir = input_dir or data_dir / "downloads"
    output_dir = output_dir or data_dir / "filtered"

    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return False

    output_dir.mkdir(parents=True, exist_ok=True)

    # Create filter instance
    quality_filter = filter_class(**filter_config)

    logger.info(f"Input: {input_dir}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Using {NUM_WORKERS} workers")
    logger.info(f"Filter config: {filter_config}")

    # Find all dataset subdirectories with parquet files
    dataset_dirs = set()
    for parquet_file in input_dir.rglob("*.parquet"):
        # Get the top-level dataset directory
        rel_path = parquet_file.relative_to(input_dir)
        dataset_dir = rel_path.parts[0] if len(rel_path.parts) > 1 else "."
        dataset_dirs.add(dataset_dir)

    if not dataset_dirs:
        logger.error("No parquet files found in input directory")
        return False

    logger.info(f"Found {len(dataset_dirs)} datasets to process: {sorted(dataset_dirs)}")

    all_success = True

    # Process each dataset separately to avoid schema conflicts
    for dataset_name in sorted(dataset_dirs):
        dataset_input = input_dir / dataset_name
        dataset_output = output_dir / dataset_name

        parquet_count = len(list(dataset_input.rglob("*.parquet")))
        logger.info(f"Processing dataset {dataset_name} ({parquet_count} parquet files)...")

        dataset_output.mkdir(parents=True, exist_ok=True)

        try:
            # Build pipeline for this dataset
            reader_kwargs = {
                "data_folder": str(dataset_input),
                "glob_pattern": "**/*.parquet",
            }
            if limit is not None:
                reader_kwargs["limit"] = limit

            pipeline = [
                ParquetReader(**reader_kwargs),
                quality_filter,
                ParquetWriter(
                    output_folder=str(dataset_output),
                    output_filename="${rank}.parquet",
                ),
            ]

            # Create executor for this dataset
            executor = LocalPipelineExecutor(
                pipeline=pipeline,
                tasks=min(NUM_WORKERS, parquet_count),  # Don't use more workers than files
                workers=min(NUM_WORKERS, parquet_count),
                logging_dir=str(data_dir / "logs" / "filter" / dataset_name),
            )

            # Run pipeline
            logger.info(f"Starting filtering for {dataset_name}...")
            executor.run()
            logger.info(f"Completed filtering for {dataset_name}")

        except Exception as e:
            logger.error(f"Filter failed for {dataset_name}: {e}")
            import traceback
            traceback.print_exc()
            all_success = False
            continue

    if all_success:
        logger.info("Filtering pipeline completed successfully for all datasets!")
    else:
        logger.warning("Some datasets failed filtering - check logs for details")

    return all_success


def run_minhash(
    language: str,
    input_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    workers: Optional[int] = None,
) -> bool:
    """
    Run MinHash deduplication stage for a language.

    Args:
        language: Language code (ar, tr, hi)
        input_dir: Input directory (default: data/{lang}/filtered)
        output_dir: Output directory (default: data/{lang}/deduped)
        workers: Number of workers (default: NUM_WORKERS)

    Returns:
        True if successful
    """
    from datatrove.executor import LocalPipelineExecutor
    from datatrove.pipeline.readers import ParquetReader
    from datatrove.pipeline.writers import ParquetWriter

    workers = workers or NUM_WORKERS
    logger.info(f"Starting MinHash deduplication stage for {language.upper()}")

    # Set up directories
    data_dir = get_data_dir(language)
    input_dir = input_dir or data_dir / "filtered"
    output_dir = output_dir or data_dir / "deduped"
    signatures_dir = data_dir / "minhash_signatures"
    buckets_dir = data_dir / "minhash_buckets"
    clusters_dir = data_dir / "minhash_clusters"

    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return False

    for d in [output_dir, signatures_dir, buckets_dir, clusters_dir]:
        d.mkdir(parents=True, exist_ok=True)

    logger.info(f"Input: {input_dir}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Using {workers} workers")
    logger.info(f"MinHash config: {MINHASH_CONFIG}")

    try:
        from datatrove.pipeline.dedup.minhash import MinhashConfig

        # Create MinHash config
        minhash_config = MinhashConfig(
            n_grams=MINHASH_CONFIG['n_grams'],
            num_buckets=MINHASH_CONFIG['num_buckets'],
            hashes_per_bucket=MINHASH_CONFIG['hashes_per_bucket'],
        )

        # Stage 1: Generate signatures
        logger.info("Stage 1: Generating MinHash signatures...")
        signature_pipeline = [
            ParquetReader(
                data_folder=str(input_dir),
                glob_pattern="**/*.parquet",
            ),
            MinhashDedupSignature(
                output_folder=str(signatures_dir),
                config=minhash_config,
            ),
        ]

        sig_executor = LocalPipelineExecutor(
            pipeline=signature_pipeline,
            tasks=workers,
            workers=workers,
            logging_dir=str(data_dir / "logs" / "minhash_sig"),
        )
        sig_executor.run()
        logger.info("Signature generation completed!")

        # Stage 2: Build buckets
        logger.info("Stage 2: Building MinHash buckets...")
        bucket_pipeline = [
            MinhashDedupBuckets(
                input_folder=str(signatures_dir),
                output_folder=str(buckets_dir),
            ),
        ]

        bucket_executor = LocalPipelineExecutor(
            pipeline=bucket_pipeline,
            tasks=MINHASH_CONFIG['num_buckets'],
            workers=min(workers, MINHASH_CONFIG['num_buckets']),
            logging_dir=str(data_dir / "logs" / "minhash_buckets"),
        )
        bucket_executor.run()
        logger.info("Bucket building completed!")

        # Stage 3: Cluster duplicates
        logger.info("Stage 3: Clustering duplicates...")
        cluster_pipeline = [
            MinhashDedupCluster(
                input_folder=str(buckets_dir),
                output_folder=str(clusters_dir),
            ),
        ]

        cluster_executor = LocalPipelineExecutor(
            pipeline=cluster_pipeline,
            tasks=1,  # Single task for clustering
            workers=1,
            logging_dir=str(data_dir / "logs" / "minhash_cluster"),
        )
        cluster_executor.run()
        logger.info("Clustering completed!")

        # Stage 4: Filter duplicates (process each dataset separately to avoid schema conflicts)
        logger.info("Stage 4: Filtering duplicates...")

        # Find all dataset subdirectories with parquet files
        dataset_dirs = set()
        for parquet_file in input_dir.rglob("*.parquet"):
            rel_path = parquet_file.relative_to(input_dir)
            dataset_dir = rel_path.parts[0] if len(rel_path.parts) > 1 else "."
            dataset_dirs.add(dataset_dir)

        logger.info(f"Found {len(dataset_dirs)} datasets to filter: {sorted(dataset_dirs)}")

        all_filter_success = True
        for dataset_name in sorted(dataset_dirs):
            dataset_input = input_dir / dataset_name
            dataset_output = output_dir / dataset_name

            parquet_count = len(list(dataset_input.rglob("*.parquet")))
            logger.info(f"Filtering dataset {dataset_name} ({parquet_count} parquet files)...")

            dataset_output.mkdir(parents=True, exist_ok=True)

            try:
                filter_pipeline = [
                    ParquetReader(
                        data_folder=str(dataset_input),
                        glob_pattern="**/*.parquet",
                    ),
                    MinhashDedupFilter(
                        input_folder=str(clusters_dir),
                    ),
                    ParquetWriter(
                        output_folder=str(dataset_output),
                        output_filename="${rank}.parquet",
                    ),
                ]

                filter_executor = LocalPipelineExecutor(
                    pipeline=filter_pipeline,
                    tasks=min(workers, parquet_count),
                    workers=min(workers, parquet_count),
                    logging_dir=str(data_dir / "logs" / "minhash_filter" / dataset_name),
                )
                filter_executor.run()
                logger.info(f"Completed filtering for {dataset_name}")
            except Exception as e:
                logger.error(f"Filter failed for {dataset_name}: {e}")
                import traceback
                traceback.print_exc()
                all_filter_success = False
                continue

        if all_filter_success:
            logger.info("MinHash deduplication completed successfully!")
        else:
            logger.warning("Some datasets failed during MinHash filtering - check logs")

        return True

    except Exception as e:
        logger.error(f"MinHash stage failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all(language: str, dry_run: bool = False) -> bool:
    """
    Run all pipeline stages for a language.

    Args:
        language: Language code (ar, tr, hi)
        dry_run: If True for download, only print commands

    Returns:
        True if all stages successful
    """
    logger.info(f"Running full pipeline for {language.upper()}")

    # Download
    logger.info("=" * 60)
    logger.info("STAGE 1: Download")
    logger.info("=" * 60)
    if not run_download(language, dry_run):
        logger.error("Download stage failed")
        return False

    # Filter
    logger.info("=" * 60)
    logger.info("STAGE 2: Quality Filtering")
    logger.info("=" * 60)
    if not run_filter(language):
        logger.error("Filter stage failed")
        return False

    # MinHash Deduplication
    logger.info("=" * 60)
    logger.info("STAGE 3: MinHash Deduplication")
    logger.info("=" * 60)
    if not run_minhash(language):
        logger.error("MinHash stage failed")
        return False

    logger.info("=" * 60)
    logger.info(f"Full pipeline for {language.upper()} completed successfully!")
    logger.info("=" * 60)

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Unified Pipeline Runner for Multi-Language Pretraining Data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Download Turkish datasets
    python run_pipeline.py --language tr --stage download

    # Run quality filtering for Hindi
    python run_pipeline.py --language hi --stage filter

    # Run full pipeline for Turkish
    python run_pipeline.py --language tr --stage all

    # Print download commands without executing
    python run_pipeline.py --language hi --stage download --dry-run
        """
    )

    parser.add_argument(
        "--language", "-l",
        required=True,
        choices=["ar", "tr", "hi", "it", "th"],
        help="Language to process (ar=Arabic, tr=Turkish, hi=Hindi, it=Italian, th=Thai)"
    )

    parser.add_argument(
        "--stage", "-s",
        required=True,
        choices=["download", "filter", "minhash", "all"],
        help="Pipeline stage to run"
    )

    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="For download stage: print commands without executing"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of documents to process (for testing)"
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Override input directory"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override output directory"
    )

    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=None,
        help="Number of workers (default: CPU cores - 2). Use lower values to reduce RAM usage."
    )

    args = parser.parse_args()

    actual_workers = args.workers or NUM_WORKERS
    logger.info(f"Pipeline Runner - Language: {args.language.upper()}, Stage: {args.stage}")
    logger.info(f"Using {actual_workers} workers")

    success = False

    if args.stage == "download":
        success = run_download(args.language, args.dry_run)
    elif args.stage == "filter":
        success = run_filter(args.language, args.input_dir, args.output_dir, args.limit)
    elif args.stage == "minhash":
        success = run_minhash(args.language, args.input_dir, args.output_dir, actual_workers)
    elif args.stage == "all":
        success = run_all(args.language, args.dry_run)

    if success:
        logger.info("Stage completed successfully!")
    else:
        logger.error("Stage failed!")
        exit(1)


if __name__ == "__main__":
    main()
