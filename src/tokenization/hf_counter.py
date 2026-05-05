"""HuggingFace dataset streaming token counter with parallel processing."""
import itertools
import logging
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, Generator, List, Optional, Tuple

from datasets import load_dataset
from huggingface_hub import HfApi

logger = logging.getLogger(__name__)

# Global tokenizer for multiprocessing (initialized per worker)
_tokenizer = None


def _get_tokenizer(model_name: str):
    """Get or initialize tokenizer (lazy loading for workers)."""
    global _tokenizer
    if _tokenizer is None:
        from transformers import AutoTokenizer
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
    return _tokenizer


def _tokenize_batch(texts: List[str], model_name: str) -> List[int]:
    """Tokenize a batch of texts and return token counts.

    This function runs in worker processes.
    """
    tokenizer = _get_tokenizer(model_name)
    counts = []
    for text in texts:
        if text:
            counts.append(len(tokenizer.encode(text, add_special_tokens=False)))
        else:
            counts.append(0)
    return counts


def decompose_to_pairs(sources: List[str], token_count: int) -> List[Tuple[frozenset, int]]:
    """Decompose multi-source document into pairwise overlaps.

    For sources = ["A", "B", "C"] and token_count = 100:
    Returns pairs: (A,B)=100, (A,C)=100, (B,C)=100

    Each pair gets FULL token count because the document
    represents overlap between those sources.
    """
    if len(sources) < 2:
        return []
    return [
        (frozenset({a, b}), token_count)
        for a, b in itertools.combinations(sorted(sources), 2)
    ]


def get_dataset_subsets(dataset_name: str) -> List[str]:
    """Dynamically discover available subsets via HuggingFace Hub API."""
    api = HfApi()
    info = api.dataset_info(dataset_name)

    # Extract subset/config names from dataset card
    if info.card_data and hasattr(info.card_data, 'configs') and info.card_data.configs:
        configs = info.card_data.configs
        # Handle both dict and object configs
        if isinstance(configs[0], dict):
            return [config['config_name'] for config in configs]
        else:
            return [config.config_name for config in configs]

    # Fallback: try to get from dataset builder configs
    try:
        from datasets import get_dataset_config_names
        return get_dataset_config_names(dataset_name)
    except Exception as e:
        logger.warning(f"Could not get configs for {dataset_name}: {e}")
        return ["default"]


@dataclass
class SourceTokenStats:
    """Token statistics for a single source."""
    tokens: int = 0
    documents: int = 0


@dataclass
class PairwiseTokenStats:
    """Pairwise overlap token statistics for consensus subsets."""
    pair_tokens: Dict[frozenset, int] = field(default_factory=dict)
    pair_docs: Dict[frozenset, int] = field(default_factory=dict)

    def add(self, pair: frozenset, tokens: int, docs: int = 1):
        """Add tokens and docs for a pair."""
        if pair not in self.pair_tokens:
            self.pair_tokens[pair] = 0
            self.pair_docs[pair] = 0
        self.pair_tokens[pair] += tokens
        self.pair_docs[pair] += docs


@dataclass
class DatasetTokenResults:
    """Token counting results for a dataset subset."""
    dataset_name: str
    subset_name: str
    by_source: Dict[str, SourceTokenStats] = field(default_factory=dict)
    pairwise: PairwiseTokenStats = field(default_factory=PairwiseTokenStats)
    total_tokens: int = 0
    total_documents: int = 0

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "dataset_name": self.dataset_name,
            "subset_name": self.subset_name,
            "by_source": {
                src: {"tokens": stats.tokens, "documents": stats.documents}
                for src, stats in self.by_source.items()
            },
            "pairwise": {
                "|".join(sorted(pair)): {"tokens": tokens, "documents": self.pairwise.pair_docs[pair]}
                for pair, tokens in self.pairwise.pair_tokens.items()
            },
            "total_tokens": self.total_tokens,
            "total_documents": self.total_documents,
        }


def stream_dataset_with_source(
    dataset_name: str,
    subset_name: str,
    max_docs: Optional[int] = None,
) -> Generator[Tuple[str, List[str]], None, None]:
    """Stream dataset yielding (text, source) tuples.

    For standard subsets, source is a single-item list.
    For consensus subsets, source is a list of multiple sources.
    """
    try:
        dataset = load_dataset(
            dataset_name,
            subset_name,
            streaming=True,
            split="train",
        )
    except Exception as e:
        logger.error(f"Failed to load {dataset_name}/{subset_name}: {e}")
        return

    count = 0
    for example in dataset:
        text = example.get("text", "")
        source = example.get("source", "unknown")

        # Handle both string and list sources
        if isinstance(source, str):
            source = [source]
        elif not isinstance(source, list):
            source = [str(source)]

        yield text, source

        count += 1
        if max_docs and count >= max_docs:
            break


class HFTokenCounter:
    """
    HuggingFace dataset streaming token counter with parallel processing.

    Two-level parallelism:
    1. Dataset/Subset Level (ThreadPoolExecutor): Stream multiple (dataset, subset)
       combinations concurrently. Uses threads because main bottleneck is network I/O.
    2. Tokenization Level (ProcessPoolExecutor): Batch texts and tokenize in parallel
       workers. This is CPU-bound work benefiting from multiprocessing.
    """

    DEFAULT_DATASETS = [
        "AdaMLLab/ThaiMix",
        "AdaMLLab/HinMix",
        "AdaMLLab/TurMix",
    ]

    def __init__(self, model_name: str = "meta-llama/Llama-3.2-3B"):
        """Initialize token counter.

        Args:
            model_name: HuggingFace model name for tokenizer
        """
        self.model_name = model_name
        # Verify tokenizer loads correctly on init
        from transformers import AutoTokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        logger.info(f"Initialized HFTokenCounter with {model_name}")

    def count_subset(
        self,
        dataset_name: str,
        subset_name: str,
        num_workers: int = 4,
        batch_size: int = 1000,
        max_docs: Optional[int] = None,
    ) -> DatasetTokenResults:
        """Count tokens in a single dataset subset with parallel tokenization.

        Args:
            dataset_name: HuggingFace dataset name
            subset_name: Subset/config name
            num_workers: Number of tokenization workers
            batch_size: Batch size for tokenization
            max_docs: Limit documents processed (for testing)

        Returns:
            DatasetTokenResults with per-source and pairwise statistics
        """
        results = DatasetTokenResults(
            dataset_name=dataset_name,
            subset_name=subset_name,
        )

        is_consensus = "consensus" in subset_name.lower()

        # Collect batches of texts and sources
        texts_batch = []
        sources_batch = []

        logger.info(f"Streaming {dataset_name}/{subset_name}...")

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            pending_futures = []

            for text, source in stream_dataset_with_source(dataset_name, subset_name, max_docs):
                texts_batch.append(text)
                sources_batch.append(source)

                # Process batch when full
                if len(texts_batch) >= batch_size:
                    future = executor.submit(_tokenize_batch, texts_batch.copy(), self.model_name)
                    pending_futures.append((future, sources_batch.copy()))
                    texts_batch.clear()
                    sources_batch.clear()

                    # Process completed futures to avoid memory buildup
                    pending_futures = self._process_completed_futures(
                        pending_futures, results, is_consensus
                    )

            # Process remaining batch
            if texts_batch:
                future = executor.submit(_tokenize_batch, texts_batch.copy(), self.model_name)
                pending_futures.append((future, sources_batch.copy()))

            # Wait for all remaining futures
            for future, sources in pending_futures:
                token_counts = future.result()
                self._aggregate_results(token_counts, sources, results, is_consensus)

        logger.info(
            f"Completed {dataset_name}/{subset_name}: "
            f"{results.total_tokens:,} tokens, {results.total_documents:,} documents"
        )

        return results

    def _process_completed_futures(
        self,
        pending_futures: List,
        results: DatasetTokenResults,
        is_consensus: bool,
    ) -> List:
        """Process completed futures without blocking, return remaining."""
        remaining = []
        for future, sources in pending_futures:
            if future.done():
                token_counts = future.result()
                self._aggregate_results(token_counts, sources, results, is_consensus)
            else:
                remaining.append((future, sources))
        return remaining

    def _aggregate_results(
        self,
        token_counts: List[int],
        sources_list: List[List[str]],
        results: DatasetTokenResults,
        is_consensus: bool,
    ):
        """Aggregate token counts into results."""
        for tokens, sources in zip(token_counts, sources_list):
            results.total_tokens += tokens
            results.total_documents += 1

            # Aggregate by source
            for src in sources:
                if src not in results.by_source:
                    results.by_source[src] = SourceTokenStats()
                results.by_source[src].tokens += tokens
                results.by_source[src].documents += 1

            # For consensus subsets, also track pairwise overlaps
            if is_consensus and len(sources) >= 2:
                for pair, pair_tokens in decompose_to_pairs(sources, tokens):
                    results.pairwise.add(pair, pair_tokens)

    def count_datasets(
        self,
        datasets: Optional[List[str]] = None,
        num_workers: int = 4,
        parallel_datasets: int = 3,
        batch_size: int = 1000,
        max_docs: Optional[int] = None,
    ) -> Dict[str, List[DatasetTokenResults]]:
        """Count tokens across multiple datasets in parallel.

        Args:
            datasets: List of dataset names (default: DEFAULT_DATASETS)
            num_workers: Number of tokenization workers per stream
            parallel_datasets: Number of concurrent dataset streams
            batch_size: Batch size for tokenization
            max_docs: Limit documents per subset (for testing)

        Returns:
            Dict mapping dataset name to list of subset results
        """
        datasets = datasets or self.DEFAULT_DATASETS

        # Discover all (dataset, subset) combinations
        tasks = []
        for dataset_name in datasets:
            logger.info(f"Discovering subsets for {dataset_name}...")
            try:
                subsets = get_dataset_subsets(dataset_name)
                logger.info(f"  Found subsets: {subsets}")
                for subset in subsets:
                    tasks.append((dataset_name, subset))
            except Exception as e:
                logger.error(f"Failed to get subsets for {dataset_name}: {e}")

        logger.info(f"Processing {len(tasks)} dataset/subset combinations...")

        # Process subsets with thread pool (I/O bound streaming)
        all_results: Dict[str, List[DatasetTokenResults]] = {d: [] for d in datasets}

        with ThreadPoolExecutor(max_workers=parallel_datasets) as executor:
            futures = {
                executor.submit(
                    self.count_subset,
                    dataset_name,
                    subset_name,
                    num_workers,
                    batch_size,
                    max_docs,
                ): (dataset_name, subset_name)
                for dataset_name, subset_name in tasks
            }

            for future in as_completed(futures):
                dataset_name, subset_name = futures[future]
                try:
                    result = future.result()
                    all_results[dataset_name].append(result)
                except Exception as e:
                    logger.error(f"Failed to process {dataset_name}/{subset_name}: {e}")

        return all_results


__all__ = ["HFTokenCounter", "DatasetTokenResults", "SourceTokenStats", "PairwiseTokenStats", "get_dataset_subsets"]
