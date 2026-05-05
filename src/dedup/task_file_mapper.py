"""
Task file mapper for minhash deduplication artifacts.

Maps (task_rank, doc_id) tuples from .dups files back to their original
source and file location. This is needed because minhash stores document
IDs as cumulative indices within each task's file list.

Datatrove's ParquetReader distributes files using stride pattern:
    files[rank::num_tasks]

So for 54 tasks and 217 files:
    - Task 0 gets files[0, 54, 108, 162, ...]
    - Task 1 gets files[1, 55, 109, 163, ...]
    - etc.

This module reconstructs that mapping to trace duplicate pairs back
to their original sources.
"""
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a parquet file."""
    filepath: Path
    source: str
    num_rows: int
    cumulative_start: int  # Starting doc_id for this file within task


class TaskFileMapper:
    """
    Maps minhash task/doc IDs back to source and file location.

    Reconstructs datatrove's file distribution pattern to enable
    tracing duplicate pairs back to their original sources.
    """

    def __init__(self, filtered_dir: Path, num_tasks: int):
        """
        Initialize the mapper by scanning filtered directory.

        Args:
            filtered_dir: Path to filtered/ directory
            num_tasks: Number of tasks used in minhash signature generation
        """
        self.filtered_dir = Path(filtered_dir)
        self.num_tasks = num_tasks

        # Enumerate all files in sorted order (same as datatrove)
        self.all_files = self._enumerate_files()
        logger.info(f"Found {len(self.all_files)} parquet files in {filtered_dir}")

        # Build per-task file mappings
        self.task_files: Dict[int, List[FileInfo]] = {}
        self._build_task_mappings()

    def _enumerate_files(self) -> List[Tuple[Path, str]]:
        """
        Enumerate all parquet files in sorted order with their source.

        Returns list of (filepath, source_name) tuples sorted by path.
        Datatrove uses glob("**/*.parquet") which returns paths in sorted order.
        """
        files = []
        for parquet_file in sorted(self.filtered_dir.rglob("*.parquet")):
            # Extract source from path: filtered/SOURCE/... or filtered/SOURCE/subdir/...
            rel_path = parquet_file.relative_to(self.filtered_dir)
            source = rel_path.parts[0]  # Top-level directory is the source
            files.append((parquet_file, source))
        return files

    def _build_task_mappings(self):
        """Build per-task file lists using datatrove's stride distribution."""
        logger.info(f"Building task mappings for {self.num_tasks} tasks...")

        for rank in range(self.num_tasks):
            # Datatrove distributes files using stride: files[rank::num_tasks]
            task_file_indices = list(range(rank, len(self.all_files), self.num_tasks))

            cumulative = 0
            self.task_files[rank] = []

            for idx in task_file_indices:
                filepath, source = self.all_files[idx]

                # Get row count from parquet metadata (fast, doesn't read data)
                try:
                    metadata = pq.read_metadata(filepath)
                    num_rows = metadata.num_rows
                except Exception as e:
                    logger.warning(f"Failed to read metadata for {filepath}: {e}")
                    num_rows = 0

                self.task_files[rank].append(FileInfo(
                    filepath=filepath,
                    source=source,
                    num_rows=num_rows,
                    cumulative_start=cumulative,
                ))
                cumulative += num_rows

            if rank % 10 == 0 or rank == self.num_tasks - 1:
                total_docs = cumulative
                logger.debug(f"Task {rank}: {len(self.task_files[rank])} files, {total_docs:,} docs")

    def lookup(self, task_rank: int, doc_id: int) -> Optional[Tuple[str, Path, int]]:
        """
        Look up the source and file for a document.

        Args:
            task_rank: Task rank (0-indexed)
            doc_id: Cumulative document index within task

        Returns:
            Tuple of (source_name, filepath, local_row_index) or None if not found
        """
        if task_rank not in self.task_files:
            logger.warning(f"Unknown task rank: {task_rank}")
            return None

        files = self.task_files[task_rank]

        # Binary search for the file containing this doc_id
        lo, hi = 0, len(files)
        while lo < hi:
            mid = (lo + hi) // 2
            file_info = files[mid]
            file_end = file_info.cumulative_start + file_info.num_rows

            if doc_id < file_info.cumulative_start:
                hi = mid
            elif doc_id >= file_end:
                lo = mid + 1
            else:
                # Found the file
                local_idx = doc_id - file_info.cumulative_start
                return (file_info.source, file_info.filepath, local_idx)

        logger.warning(f"Doc ID {doc_id} not found in task {task_rank}")
        return None

    def get_source(self, task_rank: int, doc_id: int) -> Optional[str]:
        """
        Get just the source name for a document (more efficient if that's all you need).

        Args:
            task_rank: Task rank (0-indexed)
            doc_id: Cumulative document index within task

        Returns:
            Source name or None if not found
        """
        result = self.lookup(task_rank, doc_id)
        return result[0] if result else None

    def get_task_doc_count(self, task_rank: int) -> int:
        """Get total document count for a task."""
        if task_rank not in self.task_files:
            return 0
        files = self.task_files[task_rank]
        if not files:
            return 0
        last_file = files[-1]
        return last_file.cumulative_start + last_file.num_rows

    def get_all_sources(self) -> List[str]:
        """Get list of all unique source names."""
        return sorted(set(source for _, source in self.all_files))

    def get_total_docs(self) -> int:
        """Get total document count across all tasks."""
        return sum(self.get_task_doc_count(rank) for rank in range(self.num_tasks))


__all__ = ["TaskFileMapper", "FileInfo"]
