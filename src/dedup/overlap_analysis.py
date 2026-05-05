"""
Pairwise overlap analysis between data sources.

Computes overlap statistics between pairs of sources based on content hashes.
Can optionally count tokens in overlapping documents using Llama-3.2-3B tokenizer.

This analysis should be run AFTER filtering and BEFORE or AFTER MinHash dedup
to understand how much content is shared between different data sources.

Usage:
    python -m src.dedup.overlap_analysis --language tr --count-tokens
    python scripts/run_overlap_analysis.py --language hi --pairs fineweb2,culturax
"""
import itertools
import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pyarrow.parquet as pq

from src.utils.id_generator import generate_id
from src.config.common import DATA_DIR, NUM_WORKERS

logger = logging.getLogger(__name__)


def compute_source_hashes(
    source_dir: Path,
    source_name: str,
) -> Dict[str, str]:
    """
    Compute content hashes for all documents in a source directory.

    Args:
        source_dir: Directory containing parquet files for this source
        source_name: Name of the source (for logging)

    Returns:
        Dict mapping content hash -> text (stores one representative text per hash)
    """
    hash_to_text = {}
    parquet_files = sorted(source_dir.glob("**/*.parquet"))

    logger.info(f"  Processing {source_name}: {len(parquet_files)} files")

    for pf in parquet_files:
        try:
            table = pq.read_table(pf, columns=["text"])
            for i in range(table.num_rows):
                text = table["text"][i].as_py()
                if text:
                    content_hash = generate_id(text)
                    if content_hash not in hash_to_text:
                        hash_to_text[content_hash] = text
        except Exception as e:
            logger.warning(f"  Error reading {pf}: {e}")

    logger.info(f"  {source_name}: {len(hash_to_text):,} unique documents")
    return hash_to_text


def count_tokens_for_hashes(
    hashes: Set[str],
    hash_to_text: Dict[str, str],
    tokenizer,
) -> int:
    """
    Count tokens for documents with given hashes.

    Args:
        hashes: Set of content hashes to count
        hash_to_text: Dict mapping hash -> text
        tokenizer: HuggingFace tokenizer

    Returns:
        Total token count
    """
    total_tokens = 0
    for h in hashes:
        if h in hash_to_text:
            text = hash_to_text[h]
            total_tokens += len(tokenizer.encode(text, add_special_tokens=False))
    return total_tokens


def compute_pairwise_overlap(
    source_a_hashes: Set[str],
    source_b_hashes: Set[str],
) -> Set[str]:
    """
    Compute overlapping hashes between two sources.

    Args:
        source_a_hashes: Set of content hashes from source A
        source_b_hashes: Set of content hashes from source B

    Returns:
        Set of overlapping hashes
    """
    return source_a_hashes & source_b_hashes


def analyze_pairwise_overlaps(
    language: str,
    data_dir: Optional[Path] = None,
    stage: str = "filtered",
    source_pairs: Optional[List[Tuple[str, str]]] = None,
    count_tokens: bool = True,
    output_path: Optional[Path] = None,
) -> Dict:
    """
    Analyze pairwise overlaps between all source pairs for a language.

    Args:
        language: Language code (e.g., "tr", "hi", "ar")
        data_dir: Base data directory (default: DATA_DIR)
        stage: Pipeline stage to analyze ("filtered" or "deduped")
        source_pairs: Specific pairs to analyze (default: all pairs)
        count_tokens: Whether to count tokens in overlapping docs (default: True)
        output_path: Path to save JSON results (default: auto-generated)

    Returns:
        Dict with overlap statistics
    """
    data_dir = Path(data_dir) if data_dir else DATA_DIR
    stage_dir = data_dir / language / stage

    if not stage_dir.exists():
        raise FileNotFoundError(f"Stage directory not found: {stage_dir}")

    # Find all source directories
    source_dirs = [d for d in stage_dir.iterdir() if d.is_dir() and d.name != "misc"]
    source_names = sorted([d.name for d in source_dirs])

    logger.info(f"Analyzing pairwise overlaps for {language.upper()}")
    logger.info(f"Stage: {stage}")
    logger.info(f"Sources: {source_names}")
    logger.info(f"Count tokens: {count_tokens}")

    # Initialize tokenizer if counting tokens
    tokenizer = None
    if count_tokens:
        try:
            from transformers import AutoTokenizer
            logger.info("Loading Llama-3.2-3B tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-3B")
        except Exception as e:
            logger.warning(f"Could not load tokenizer: {e}")
            logger.warning("Proceeding without token counting")
            count_tokens = False

    # Compute hashes for each source
    logger.info("\n" + "=" * 50)
    logger.info("Computing content hashes per source...")
    logger.info("=" * 50)

    source_hashes = {}  # source_name -> set of hashes
    source_hash_to_text = {}  # source_name -> {hash -> text}

    for source_name in source_names:
        source_dir = stage_dir / source_name
        hash_to_text = compute_source_hashes(source_dir, source_name)
        source_hashes[source_name] = set(hash_to_text.keys())
        if count_tokens:
            source_hash_to_text[source_name] = hash_to_text

    # Determine pairs to analyze
    if source_pairs is None:
        # All possible pairs
        source_pairs = list(itertools.combinations(source_names, 2))
    else:
        # Validate provided pairs
        valid_pairs = []
        for a, b in source_pairs:
            if a in source_names and b in source_names:
                valid_pairs.append((a, b))
            else:
                logger.warning(f"Skipping invalid pair: {a}, {b}")
        source_pairs = valid_pairs

    logger.info(f"\nAnalyzing {len(source_pairs)} source pairs...")

    # Compute pairwise overlaps
    logger.info("\n" + "=" * 50)
    logger.info("Computing pairwise overlaps...")
    logger.info("=" * 50)

    results = {
        "language": language,
        "stage": stage,
        "timestamp": datetime.now().isoformat(),
        "sources": {},
        "pairwise_overlaps": [],
    }

    # Source-level stats
    for source_name in source_names:
        source_stats = {
            "name": source_name,
            "unique_documents": len(source_hashes[source_name]),
        }
        if count_tokens and source_name in source_hash_to_text:
            total_tokens = count_tokens_for_hashes(
                source_hashes[source_name],
                source_hash_to_text[source_name],
                tokenizer,
            )
            source_stats["total_tokens"] = total_tokens
        results["sources"][source_name] = source_stats

    # Pairwise overlaps
    for source_a, source_b in source_pairs:
        overlap_hashes = compute_pairwise_overlap(
            source_hashes[source_a],
            source_hashes[source_b],
        )

        pair_result = {
            "source_a": source_a,
            "source_b": source_b,
            "overlap_documents": len(overlap_hashes),
            "overlap_pct_of_a": 100 * len(overlap_hashes) / len(source_hashes[source_a])
            if source_hashes[source_a] else 0,
            "overlap_pct_of_b": 100 * len(overlap_hashes) / len(source_hashes[source_b])
            if source_hashes[source_b] else 0,
        }

        if count_tokens and overlap_hashes:
            # Use hash_to_text from either source (content is identical)
            hash_to_text = source_hash_to_text.get(source_a, {})
            overlap_tokens = count_tokens_for_hashes(overlap_hashes, hash_to_text, tokenizer)
            pair_result["overlap_tokens"] = overlap_tokens

        results["pairwise_overlaps"].append(pair_result)

        # Log progress
        logger.info(
            f"  {source_a} <-> {source_b}: "
            f"{len(overlap_hashes):,} overlapping docs "
            f"({pair_result['overlap_pct_of_a']:.1f}% of {source_a}, "
            f"{pair_result['overlap_pct_of_b']:.1f}% of {source_b})"
        )

    # Save results
    output_path = output_path or (data_dir / language / f"overlap_analysis_{stage}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"\nResults saved to: {output_path}")

    # Print summary
    _print_summary(results)

    return results


def _print_summary(results: Dict):
    """Print a human-readable summary of overlap analysis."""
    print("\n" + "=" * 70)
    print(f"OVERLAP ANALYSIS SUMMARY - {results['language'].upper()} ({results['stage']})")
    print("=" * 70)

    print("\nSource Statistics:")
    print("-" * 50)
    for name, stats in results["sources"].items():
        line = f"  {name:<20} {stats['unique_documents']:>12,} docs"
        if "total_tokens" in stats:
            line += f"  {stats['total_tokens']:>15,} tokens"
        print(line)

    print("\nPairwise Overlaps:")
    print("-" * 70)
    print(f"  {'Source A':<15} {'Source B':<15} {'Overlap':<12} {'% of A':<10} {'% of B':<10} {'Tokens':<15}")
    print("-" * 70)

    for pair in results["pairwise_overlaps"]:
        tokens_str = f"{pair.get('overlap_tokens', 'N/A'):,}" if "overlap_tokens" in pair else "N/A"
        print(
            f"  {pair['source_a']:<15} "
            f"{pair['source_b']:<15} "
            f"{pair['overlap_documents']:<12,} "
            f"{pair['overlap_pct_of_a']:<10.1f} "
            f"{pair['overlap_pct_of_b']:<10.1f} "
            f"{tokens_str:<15}"
        )

    print("=" * 70)


def main():
    """CLI entry point for overlap analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze pairwise overlaps between data sources"
    )
    parser.add_argument(
        "--language", "-l", required=True,
        help="Language code (e.g., tr, hi, ar)"
    )
    parser.add_argument(
        "--stage", "-s", default="filtered",
        choices=["filtered", "deduped"],
        help="Pipeline stage to analyze (default: filtered)"
    )
    parser.add_argument(
        "--pairs", "-p", type=str, default=None,
        help="Comma-separated source pairs to analyze (e.g., 'fineweb2,culturax;hplt2,c4')"
    )
    parser.add_argument(
        "--no-count-tokens", action="store_true",
        help="Disable token counting (faster but less info)"
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output JSON file path"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Parse pairs if provided
    source_pairs = None
    if args.pairs:
        source_pairs = []
        for pair_str in args.pairs.split(";"):
            parts = pair_str.split(",")
            if len(parts) == 2:
                source_pairs.append((parts[0].strip(), parts[1].strip()))

    output_path = Path(args.output) if args.output else None

    analyze_pairwise_overlaps(
        language=args.language,
        stage=args.stage,
        source_pairs=source_pairs,
        count_tokens=not args.no_count_tokens,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()
