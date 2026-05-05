"""
Deduplication modules using DataTrove.

MinHash Deduplication:
    Uses DataTrove's MinhashDedupSignature, MinhashDedupBuckets,
    MinhashDedupCluster, and MinhashDedupFilter stages.

Sentence Deduplication:
    Uses DataTrove's SentenceDedupSignature, SentenceFindDedups,
    and SentenceDedupFilter stages.

Consensus Building:
    Extracts documents appearing in 2+ sources.
    See consensus.py for the build_consensus function.

Configuration:
    See src/config/common.py for MINHASH_CONFIG parameters.
"""

from datatrove.pipeline.dedup import (
    MinhashDedupSignature,
    MinhashDedupBuckets,
    MinhashDedupCluster,
    MinhashDedupFilter,
    SentenceDedupSignature,
    SentenceFindDedups,
    SentenceDedupFilter,
)

from .consensus import build_consensus
from .minhash_consensus import build_minhash_consensus
from .task_file_mapper import TaskFileMapper
from .overlap_analysis import analyze_pairwise_overlaps

__all__ = [
    "MinhashDedupSignature",
    "MinhashDedupBuckets",
    "MinhashDedupCluster",
    "MinhashDedupFilter",
    "SentenceDedupSignature",
    "SentenceFindDedups",
    "SentenceDedupFilter",
    "build_consensus",
    "build_minhash_consensus",
    "TaskFileMapper",
    "analyze_pairwise_overlaps",
]
