"""
Consensus subset builder - memory-efficient two-pass algorithm.

Finds documents appearing in 2+ sources and outputs them with the
CONSENSUS_SCHEMA: {'text', 'id', 'source'} where source is a list.

Two-pass algorithm:
1. First pass: Build hash -> sources mapping (don't store full text)
2. Second pass: Re-read data and collect documents whose hashes appear in 2+ sources
"""
import logging
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set, Optional

import pyarrow as pa
import pyarrow.parquet as pq

from src.utils.id_generator import generate_id
from src.config.schema import CONSENSUS_SCHEMA
from src.config.common import PARQUET_CONFIG, DATA_DIR

logger = logging.getLogger(__name__)


def _pass1_build_hash_index(deduped_dir: Path, skip_sources: Optional[Set[str]] = None) -> Dict[str, Set[str]]:
    """
    Pass 1: Build hash -> sources mapping.

    Only stores hash and source names, not full document text.
    Memory efficient - just the hashes.

    Args:
        deduped_dir: Directory containing per-source deduped subdirectories
        skip_sources: Source names to skip (e.g., {"misc"})

    Returns:
        Dict mapping text hash -> set of source names
    """
    skip_sources = skip_sources or {"misc"}
    hash_to_sources = defaultdict(set)

    for source_dir in sorted(deduped_dir.iterdir()):
        if not source_dir.is_dir():
            continue
        source = source_dir.name
        if source in skip_sources:
            continue

        logger.info(f"Pass 1 - Indexing source: {source}")
        parquet_files = sorted(source_dir.glob("*.parquet"))

        for pf in parquet_files:
            table = pq.read_table(pf, columns=["text"])
            for i in range(table.num_rows):
                text = table["text"][i].as_py()
                if text:
                    text_hash = generate_id(text)
                    hash_to_sources[text_hash].add(source)

            logger.info(f"  {pf.name}: {table.num_rows:,} docs indexed")

    return hash_to_sources


def _pass2_extract_consensus(
    deduped_dir: Path,
    multi_source_hashes: Set[str],
    skip_sources: Optional[Set[str]] = None,
) -> Dict[str, dict]:
    """
    Pass 2: Re-read data and extract documents with multi-source hashes.

    Args:
        deduped_dir: Directory containing per-source deduped subdirectories
        multi_source_hashes: Set of hashes appearing in 2+ sources
        skip_sources: Source names to skip

    Returns:
        Dict: hash -> {'text': str, 'sources': set}
    """
    skip_sources = skip_sources or {"misc"}
    consensus_docs = {}

    for source_dir in sorted(deduped_dir.iterdir()):
        if not source_dir.is_dir():
            continue
        source = source_dir.name
        if source in skip_sources:
            continue

        logger.info(f"Pass 2 - Extracting from source: {source}")
        parquet_files = sorted(source_dir.glob("*.parquet"))

        for pf in parquet_files:
            table = pq.read_table(pf, columns=["text"])
            found_in_file = 0

            for i in range(table.num_rows):
                text = table["text"][i].as_py()
                if not text:
                    continue

                text_hash = generate_id(text)

                if text_hash in multi_source_hashes:
                    if text_hash not in consensus_docs:
                        consensus_docs[text_hash] = {
                            "text": text,
                            "sources": set(),
                        }

                    consensus_docs[text_hash]["sources"].add(source)
                    found_in_file += 1

            if found_in_file > 0:
                logger.info(f"  {pf.name}: found {found_in_file:,} consensus docs")

    return consensus_docs


def _save_consensus_parquet(
    docs: Dict[str, dict],
    output_dir: Path,
    max_files: int = 200,
) -> int:
    """
    Save consensus documents to parquet files with CONSENSUS_SCHEMA.

    Consolidates into max_files or fewer files with proper Parquet settings.

    Args:
        docs: Dict of hash -> {'text': str, 'sources': set}
        output_dir: Output directory
        max_files: Maximum number of output files

    Returns:
        Number of documents written
    """
    if not docs:
        logger.warning("No consensus documents to save!")
        return 0

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare data
    doc_list = list(docs.items())
    total_docs = len(doc_list)

    # Calculate docs per file to stay under max_files
    docs_per_file = math.ceil(total_docs / max_files)
    logger.info(f"Writing {total_docs:,} docs to ~{min(max_files, total_docs)} files")

    file_idx = 0
    for batch_start in range(0, total_docs, docs_per_file):
        batch_end = min(batch_start + docs_per_file, total_docs)
        batch = doc_list[batch_start:batch_end]

        rows = []
        for text_hash, doc in batch:
            rows.append({
                "text": doc["text"],
                "id": text_hash,
                "source": sorted(doc["sources"]),  # List of sources
            })

        table = pa.Table.from_pylist(rows, schema=CONSENSUS_SCHEMA)

        output_path = output_dir / f"{file_idx:05d}.parquet"
        pq.write_table(
            table,
            output_path,
            row_group_size=PARQUET_CONFIG["row_group_size"],
            write_page_index=PARQUET_CONFIG["write_page_index"],
            compression=PARQUET_CONFIG["compression"],
        )

        logger.info(f"Wrote {len(rows):,} docs to {output_path.name}")
        file_idx += 1

    return total_docs


def build_consensus(
    language: str,
    min_sources: int = 2,
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    max_files: int = 200,
) -> Path:
    """
    Build consensus subset: documents appearing in min_sources or more.

    Uses memory-efficient two-pass algorithm:
    1. First pass: Build hash -> sources mapping
    2. Second pass: Extract documents in 2+ sources

    Output schema: {'text', 'id', 'source'} where source is a list.

    Args:
        language: Language code (e.g., "tr", "hi", "ar")
        min_sources: Minimum number of sources for consensus (default 2)
        data_dir: Base data directory (default: DATA_DIR)
        output_dir: Output directory (default: data/{language}/consensus)
        max_files: Maximum output files (default 200)

    Returns:
        Path to output directory
    """
    data_dir = Path(data_dir) if data_dir else DATA_DIR
    deduped_dir = data_dir / language / "deduped"
    output_dir = Path(output_dir) if output_dir else data_dir / language / "consensus"

    if not deduped_dir.exists():
        raise FileNotFoundError(f"Deduped directory not found: {deduped_dir}")

    logger.info(f"Building consensus subset for {language.upper()}")
    logger.info(f"Input: {deduped_dir}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Min sources: {min_sources}")

    # Pass 1: Build hash -> sources mapping
    logger.info("=" * 50)
    logger.info("PASS 1: Building hash-to-sources index...")
    logger.info("=" * 50)
    hash_to_sources = _pass1_build_hash_index(deduped_dir)
    logger.info(f"Total unique hashes: {len(hash_to_sources):,}")

    # Find multi-source hashes
    multi_source_hashes = {
        h for h, sources in hash_to_sources.items()
        if len(sources) >= min_sources
    }
    logger.info(f"Hashes appearing in {min_sources}+ sources: {len(multi_source_hashes):,}")

    if not multi_source_hashes:
        logger.info("No consensus documents found!")
        return output_dir

    # Clear hash_to_sources to free memory
    del hash_to_sources

    # Pass 2: Extract consensus documents
    logger.info("=" * 50)
    logger.info("PASS 2: Extracting consensus documents...")
    logger.info("=" * 50)
    consensus_docs = _pass2_extract_consensus(deduped_dir, multi_source_hashes)
    logger.info(f"Extracted {len(consensus_docs):,} consensus documents")

    # Save to parquet with new schema
    logger.info("=" * 50)
    logger.info("Saving consensus parquet files...")
    logger.info("=" * 50)
    num_saved = _save_consensus_parquet(consensus_docs, output_dir, max_files)

    # Print summary
    source_counts = defaultdict(int)
    for doc in consensus_docs.values():
        for source in doc["sources"]:
            source_counts[source] += 1

    logger.info("\nConsensus summary:")
    logger.info(f"  Total consensus documents: {num_saved:,}")
    logger.info("  Source participation:")
    for source, count in sorted(source_counts.items()):
        logger.info(f"    {source}: {count:,}")

    return output_dir


__all__ = ["build_consensus"]
