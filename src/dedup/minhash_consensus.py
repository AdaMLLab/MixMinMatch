"""
Minhash-based consensus builder.

Builds consensus subset by parsing .dups files from minhash deduplication
to find documents appearing in 2+ sources. This captures near-duplicates
(~80% Jaccard similarity) unlike the hash-based method which only finds
exact matches.

Memory-optimized algorithm:
1. Build a TaskFileMapper to trace task/doc IDs back to sources
2. Parse .dups files, SKIP same-source pairs to save memory
3. Build union-find clusters only for cross-source pairs
4. Identify clusters spanning 2+ sources
5. Stream extract documents and write in batches (don't hold all in memory)
"""
import gc
import logging
import math
import struct
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set, Optional, Tuple, List, Iterator

import pyarrow as pa
import pyarrow.parquet as pq

from src.config.common import DATA_DIR, PARQUET_CONFIG
from src.config.schema import CONSENSUS_SCHEMA
from src.utils.id_generator import generate_id
from .task_file_mapper import TaskFileMapper

logger = logging.getLogger(__name__)

# Batch size for writing parquet files (to limit memory)
WRITE_BATCH_SIZE = 100_000


class UnionFind:
    """
    Union-Find data structure with path compression.
    Same algorithm as datatrove's MinhashDedupCluster.
    """

    def __init__(self):
        self.parent: Dict[Tuple[int, int], Tuple[int, int]] = {}

    def find(self, x: Tuple[int, int]) -> Tuple[int, int]:
        """Find root with path compression."""
        if x not in self.parent:
            self.parent[x] = x
            return x

        if self.parent[x] == x:
            return x

        # Path compression
        self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: Tuple[int, int], b: Tuple[int, int]) -> None:
        """Union two elements."""
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def _iter_dups_file(filepath: Path) -> Iterator[Tuple[int, int, int, int]]:
    """
    Iterate over a .dups file, yielding duplicate pairs.
    Uses iterator to avoid loading all pairs into memory.
    """
    record_size = 16  # 4 uint32 values

    with open(filepath, 'rb') as f:
        while True:
            data = f.read(record_size)
            if not data:
                break
            if len(data) < record_size:
                break

            file1, doc1, file2, doc2 = struct.unpack('<4I', data)
            yield (file1, doc1, file2, doc2)


def _build_clusters_cross_source_only(
    dups_dir: Path,
    mapper: TaskFileMapper,
) -> Tuple[UnionFind, Dict[Tuple[int, int], str]]:
    """
    Parse .dups files but ONLY process cross-source pairs.

    MEMORY OPTIMIZATION: Skip same-source pairs entirely.
    This dramatically reduces memory since most duplicates are within-source.

    Args:
        dups_dir: Directory containing .dups files
        mapper: TaskFileMapper for source lookups

    Returns:
        Tuple of (UnionFind, doc_to_source mapping for cross-source docs only)
    """
    uf = UnionFind()
    # Only store single source per doc (not a set) since we only process cross-source pairs
    doc_source: Dict[Tuple[int, int], str] = {}

    dups_files = sorted(dups_dir.glob("*.dups"))
    logger.info(f"Found {len(dups_files)} .dups files in {dups_dir}")

    total_pairs = 0
    cross_source_pairs = 0

    for dups_file in dups_files:
        file_pairs = 0
        file_cross = 0

        for task1, doc1, task2, doc2 in _iter_dups_file(dups_file):
            file_pairs += 1

            # Get sources for both documents
            source1 = mapper.get_source(task1, doc1)
            source2 = mapper.get_source(task2, doc2)

            # SKIP same-source pairs - they can't contribute to consensus
            if source1 == source2:
                continue

            if source1 is None or source2 is None:
                continue

            file_cross += 1

            key1 = (task1, doc1)
            key2 = (task2, doc2)

            # Union the documents
            uf.union(key1, key2)

            # Track source for each document
            doc_source[key1] = source1
            doc_source[key2] = source2

        total_pairs += file_pairs
        cross_source_pairs += file_cross
        logger.info(f"  {dups_file.name}: {file_pairs:,} pairs, {file_cross:,} cross-source")

    logger.info(f"Total pairs: {total_pairs:,}")
    logger.info(f"Cross-source pairs: {cross_source_pairs:,} ({100*cross_source_pairs/max(1,total_pairs):.1f}%)")
    logger.info(f"Unique docs in cross-source pairs: {len(doc_source):,}")

    return uf, doc_source


def _find_multi_source_clusters(
    uf: UnionFind,
    doc_source: Dict[Tuple[int, int], str],
    min_sources: int = 2,
) -> Dict[Tuple[int, int], Set[str]]:
    """
    Find clusters that span multiple sources.

    Returns:
        Dict mapping cluster root -> set of all sources in cluster
    """
    # Aggregate sources by cluster root
    root_sources: Dict[Tuple[int, int], Set[str]] = defaultdict(set)

    for doc, source in doc_source.items():
        root = uf.find(doc)
        root_sources[root].add(source)

    # Filter to multi-source clusters
    multi_source = {
        root: sources
        for root, sources in root_sources.items()
        if len(sources) >= min_sources
    }

    logger.info(f"Clusters spanning {min_sources}+ sources: {len(multi_source):,}")

    # Log source distribution
    source_counts = defaultdict(int)
    for sources in multi_source.values():
        for s in sources:
            source_counts[s] += 1

    logger.info("Source participation in multi-source clusters:")
    for source, count in sorted(source_counts.items()):
        logger.info(f"  {source}: {count:,} clusters")

    return multi_source


def _get_representative_docs(
    multi_source_roots: Dict[Tuple[int, int], Set[str]],
    uf: UnionFind,
    doc_source: Dict[Tuple[int, int], str],
) -> Dict[Tuple[int, int], Tuple[Tuple[int, int], Set[str]]]:
    """
    For each multi-source cluster, find one representative document.

    Returns:
        Dict mapping representative doc -> (root, sources)
    """
    # Find one doc per root
    root_to_doc: Dict[Tuple[int, int], Tuple[int, int]] = {}

    for doc in doc_source.keys():
        root = uf.find(doc)
        if root in multi_source_roots and root not in root_to_doc:
            root_to_doc[root] = doc

    # Invert: doc -> (root, sources)
    doc_to_info: Dict[Tuple[int, int], Tuple[Tuple[int, int], Set[str]]] = {}
    for root, doc in root_to_doc.items():
        doc_to_info[doc] = (root, multi_source_roots[root])

    logger.info(f"Found representatives for {len(doc_to_info):,} multi-source clusters")
    return doc_to_info


def _extract_and_write_streaming(
    doc_to_info: Dict[Tuple[int, int], Tuple[Tuple[int, int], Set[str]]],
    mapper: TaskFileMapper,
    output_dir: Path,
    max_files: int = 200,
) -> int:
    """
    Extract documents and write to parquet in a streaming fashion.

    MEMORY OPTIMIZATION: Process files one at a time, write batches
    instead of collecting all documents in memory.

    Returns:
        Number of documents written
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group representatives by file for efficient reading
    file_to_reads: Dict[Path, List[Tuple[int, Tuple[int, int], Set[str]]]] = defaultdict(list)

    for doc, (root, sources) in doc_to_info.items():
        result = mapper.lookup(doc[0], doc[1])
        if result:
            source, filepath, local_idx = result
            file_to_reads[filepath].append((local_idx, doc, sources))

    logger.info(f"Need to read from {len(file_to_reads):,} parquet files")

    # Estimate docs per output file
    total_clusters = len(doc_to_info)
    docs_per_file = max(1, math.ceil(total_clusters / max_files))

    # Process and write in batches
    current_batch = []
    file_idx = 0
    total_written = 0
    files_processed = 0

    def write_batch():
        nonlocal current_batch, file_idx, total_written
        if not current_batch:
            return

        rows = []
        for text_hash, text, sources in current_batch:
            rows.append({
                "text": text,
                "id": text_hash,
                "source": sorted(sources),
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

        total_written += len(current_batch)
        logger.info(f"Wrote {len(current_batch):,} docs to {output_path.name} "
                   f"(total: {total_written:,})")
        file_idx += 1
        current_batch = []

    for filepath, reads in file_to_reads.items():
        # Sort by local index for efficient access
        reads.sort(key=lambda x: x[0])

        try:
            table = pq.read_table(filepath, columns=["text"])

            for local_idx, doc, sources in reads:
                if local_idx < table.num_rows:
                    text = table["text"][local_idx].as_py()
                    if text:
                        text_hash = generate_id(text)
                        current_batch.append((text_hash, text, sources))

                        # Write batch when it reaches target size
                        if len(current_batch) >= docs_per_file:
                            write_batch()
                else:
                    logger.warning(f"Index {local_idx} out of range for {filepath}")

            # Free memory
            del table

        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            continue

        files_processed += 1
        if files_processed % 50 == 0:
            logger.info(f"  Processed {files_processed}/{len(file_to_reads)} files")
            gc.collect()  # Help free memory

    # Write final batch
    write_batch()

    logger.info(f"Extracted and wrote {total_written:,} consensus documents")
    return total_written


def build_minhash_consensus(
    language: str,
    min_sources: int = 2,
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    max_files: int = 200,
    input_dir: Optional[Path] = None,
) -> Path:
    """
    Build consensus subset from minhash .dups artifacts.

    Memory-optimized: Only processes cross-source pairs and streams output.

    Args:
        language: Language code (e.g., "tr", "hi", "ar")
        min_sources: Minimum number of sources for consensus (default 2)
        data_dir: Base data directory (default: DATA_DIR)
        output_dir: Output directory (default: data/{language}/consensus)
        max_files: Maximum output files (default 200)
        input_dir: Override filtered directory (default: data/{language}/filtered)

    Returns:
        Path to output directory
    """
    data_dir = Path(data_dir) if data_dir else DATA_DIR
    lang_dir = data_dir / language

    filtered_dir = Path(input_dir) if input_dir else lang_dir / "filtered"
    dups_dir = lang_dir / "minhash_buckets"
    signatures_dir = lang_dir / "minhash_signatures"
    output_dir = Path(output_dir) if output_dir else lang_dir / "consensus"

    # Validate directories exist
    if not filtered_dir.exists():
        raise FileNotFoundError(f"Filtered directory not found: {filtered_dir}")
    if not dups_dir.exists():
        raise FileNotFoundError(f"Minhash buckets directory not found: {dups_dir}")

    # Determine number of tasks from signature files
    bucket_dirs = list(signatures_dir.glob("bucket_*"))
    if not bucket_dirs:
        raise FileNotFoundError(f"No bucket directories in {signatures_dir}")

    sig_files = list(bucket_dirs[0].glob("*.sig"))
    num_tasks = len(sig_files)
    if num_tasks == 0:
        raise ValueError(f"No signature files found in {bucket_dirs[0]}")

    logger.info(f"Building minhash-based consensus for {language.upper()}")
    logger.info(f"Input filtered: {filtered_dir}")
    logger.info(f"Input dups: {dups_dir}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Min sources: {min_sources}")
    logger.info(f"Detected {num_tasks} tasks from minhash artifacts")

    # Phase 1: Build task->source mapper
    logger.info("=" * 50)
    logger.info("PHASE 1: Building task-to-source mapper...")
    logger.info("=" * 50)
    mapper = TaskFileMapper(filtered_dir, num_tasks)
    logger.info(f"Total files: {len(mapper.all_files):,}")
    logger.info(f"Sources: {mapper.get_all_sources()}")

    # Phase 2: Parse .dups files (cross-source only)
    logger.info("=" * 50)
    logger.info("PHASE 2: Parsing .dups files (cross-source pairs only)...")
    logger.info("=" * 50)
    uf, doc_source = _build_clusters_cross_source_only(dups_dir, mapper)
    gc.collect()

    # Phase 3: Find multi-source clusters
    logger.info("=" * 50)
    logger.info("PHASE 3: Finding multi-source clusters...")
    logger.info("=" * 50)
    multi_source_roots = _find_multi_source_clusters(uf, doc_source, min_sources)

    if not multi_source_roots:
        logger.warning("No multi-source clusters found!")
        return output_dir

    # Phase 4: Get representative documents
    logger.info("=" * 50)
    logger.info("PHASE 4: Identifying representative documents...")
    logger.info("=" * 50)
    doc_to_info = _get_representative_docs(multi_source_roots, uf, doc_source)

    # Free large data structures we no longer need
    del multi_source_roots
    del doc_source
    del uf
    gc.collect()
    logger.info("Freed intermediate data structures")

    # Phase 5: Extract and write (streaming)
    logger.info("=" * 50)
    logger.info("PHASE 5: Extracting and writing consensus documents...")
    logger.info("=" * 50)
    num_saved = _extract_and_write_streaming(doc_to_info, mapper, output_dir, max_files)

    logger.info("\nConsensus building complete!")
    logger.info(f"  Total consensus documents: {num_saved:,}")
    logger.info(f"  Output directory: {output_dir}")

    return output_dir


__all__ = ["build_minhash_consensus"]
