"""Parallel token counting using Llama-3.2-3B tokenizer."""
import os
import logging
from pathlib import Path
from typing import Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial

import pyarrow.parquet as pq

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


def _count_file_tokens(parquet_path: str, model_name: str) -> dict:
    """
    Count tokens in a single parquet file.

    This function is designed to run in a separate process.
    """
    try:
        tokenizer = _get_tokenizer(model_name)
        table = pq.read_table(parquet_path, columns=["text"])
        texts = table["text"].to_pylist()

        token_count = 0
        for text in texts:
            if text:
                token_count += len(tokenizer.encode(text, add_special_tokens=False))

        return {
            "file": str(parquet_path),
            "tokens": token_count,
            "docs": len(texts),
            "error": None,
        }
    except Exception as e:
        return {
            "file": str(parquet_path),
            "tokens": 0,
            "docs": 0,
            "error": str(e),
        }


class TokenCounter:
    """
    Parallel token counter using Llama-3.2-3B tokenizer.

    Counts tokens across parquet files in a directory using multiprocessing
    for high throughput. Results are aggregated per file and directory.
    """

    def __init__(self, model_name: str = "meta-llama/Llama-3.2-3B"):
        """
        Initialize token counter.

        Args:
            model_name: HuggingFace model name for tokenizer
        """
        self.model_name = model_name
        # Verify tokenizer loads correctly on init
        from transformers import AutoTokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        logger.info(f"Initialized TokenCounter with {model_name}")

    def count_file(self, parquet_path: Path) -> dict:
        """
        Count tokens in a single parquet file (single-threaded).

        Args:
            parquet_path: Path to parquet file

        Returns:
            Dict with file, tokens, docs, error keys
        """
        return _count_file_tokens(str(parquet_path), self.model_name)

    def count_directory(
        self,
        directory: Path,
        num_workers: Optional[int] = None,
        glob_pattern: str = "**/*.parquet",
    ) -> dict:
        """
        Count tokens across all parquet files in directory using parallel processing.

        Args:
            directory: Directory containing parquet files
            num_workers: Number of parallel workers (default: CPU count - 2)
            glob_pattern: Glob pattern for finding parquet files

        Returns:
            Dict with total_tokens, total_docs, files (list of per-file results)
        """
        directory = Path(directory)
        files = sorted(directory.glob(glob_pattern))

        if not files:
            logger.warning(f"No parquet files found in {directory}")
            return {"total_tokens": 0, "total_docs": 0, "files": []}

        num_workers = num_workers or max(1, os.cpu_count() - 2)
        logger.info(f"Counting tokens in {len(files)} files with {num_workers} workers")

        results = []
        errors = []

        # Use ProcessPoolExecutor for true parallelism
        count_func = partial(_count_file_tokens, model_name=self.model_name)

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(count_func, str(f)): f for f in files}

            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                if result["error"]:
                    errors.append(result)

        if errors:
            logger.warning(f"{len(errors)} files had errors during token counting")

        total_tokens = sum(r["tokens"] for r in results)
        total_docs = sum(r["docs"] for r in results)

        logger.info(f"Total: {total_tokens:,} tokens across {total_docs:,} documents")

        return {
            "total_tokens": total_tokens,
            "total_docs": total_docs,
            "files": results,
        }


__all__ = ["TokenCounter"]
