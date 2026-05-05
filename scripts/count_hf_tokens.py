#!/usr/bin/env python3
"""
HuggingFace dataset token counting script.

Counts tokens in HuggingFace datasets using streaming to avoid full downloads.
Supports parallel processing and per-source token aggregation.

Usage:
    # Count tokens in all default datasets
    python scripts/count_hf_tokens.py --output hf_token_counts.json

    # Test with limited documents
    python scripts/count_hf_tokens.py --max-docs 100 --output test_results.json

    # Count specific datasets
    python scripts/count_hf_tokens.py --datasets AdaMLLab/ThaiMix AdaMLLab/HinMix

    # Adjust parallelism
    python scripts/count_hf_tokens.py --workers 8 --parallel-datasets 2 --batch-size 2000
"""
import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.common import NUM_WORKERS
from src.tokenization import HFTokenCounter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def format_number(n: int) -> str:
    """Format number with commas."""
    return f"{n:,}"


def print_results(all_results: dict):
    """Print formatted results to console."""
    print("\n" + "=" * 80)
    print("TOKEN COUNT RESULTS")
    print("=" * 80)

    for dataset_name, subset_results in all_results.items():
        print(f"\n{dataset_name}")
        print("-" * 60)

        for result in sorted(subset_results, key=lambda r: r.subset_name):
            print(f"\n  Subset: {result.subset_name}")
            print(f"  Total: {format_number(result.total_tokens)} tokens, {format_number(result.total_documents)} documents")

            if result.by_source:
                print("\n  By Source:")
                # Sort by token count descending
                sorted_sources = sorted(
                    result.by_source.items(),
                    key=lambda x: x[1].tokens,
                    reverse=True
                )
                for src, stats in sorted_sources:
                    print(f"    {src:30} {format_number(stats.tokens):>20} tokens ({format_number(stats.documents)} docs)")

            if result.pairwise.pair_tokens:
                print("\n  Pairwise Overlap (Consensus):")
                # Sort by token count descending
                sorted_pairs = sorted(
                    result.pairwise.pair_tokens.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                for pair, tokens in sorted_pairs:
                    pair_str = "|".join(sorted(pair))
                    docs = result.pairwise.pair_docs[pair]
                    print(f"    {pair_str:30} {format_number(tokens):>20} tokens ({format_number(docs)} docs)")

    print("\n" + "=" * 80)


def results_to_json(all_results: dict) -> dict:
    """Convert results to JSON-serializable format."""
    return {
        dataset_name: [r.to_dict() for r in subset_results]
        for dataset_name, subset_results in all_results.items()
    }


def main():
    parser = argparse.ArgumentParser(
        description="Count tokens in HuggingFace datasets using streaming"
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=None,
        help="Datasets to process (default: AdaMLLab/ThaiMix, AdaMLLab/HinMix, AdaMLLab/TurMix)"
    )
    parser.add_argument(
        "--model",
        default="meta-llama/Llama-3.2-3B",
        help="Tokenizer model (default: meta-llama/Llama-3.2-3B)"
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=NUM_WORKERS,
        help=f"Number of tokenization workers (default: {NUM_WORKERS})"
    )
    parser.add_argument(
        "--parallel-datasets",
        type=int,
        default=3,
        help="Number of concurrent dataset streams (default: 3)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for tokenization (default: 1000)"
    )
    parser.add_argument(
        "--max-docs",
        type=int,
        default=None,
        help="Limit docs per subset (for testing)"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="JSON output file path"
    )

    args = parser.parse_args()

    logger.info(f"Initializing token counter with model: {args.model}")
    counter = HFTokenCounter(model_name=args.model)

    datasets = args.datasets or counter.DEFAULT_DATASETS
    logger.info(f"Processing datasets: {datasets}")
    logger.info(f"Workers: {args.workers}, Parallel datasets: {args.parallel_datasets}, Batch size: {args.batch_size}")

    if args.max_docs:
        logger.info(f"Limiting to {args.max_docs} docs per subset (testing mode)")

    # Run token counting
    all_results = counter.count_datasets(
        datasets=datasets,
        num_workers=args.workers,
        parallel_datasets=args.parallel_datasets,
        batch_size=args.batch_size,
        max_docs=args.max_docs,
    )

    # Print formatted results
    print_results(all_results)

    # Save to JSON if output specified
    if args.output:
        output_path = Path(args.output)
        output_data = results_to_json(all_results)

        # Add metadata
        output_data["_metadata"] = {
            "model": args.model,
            "datasets": datasets,
            "max_docs": args.max_docs,
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
