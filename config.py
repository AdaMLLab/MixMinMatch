"""
Configuration for Multi-Language Pretraining Mix pipeline.

This file provides backward compatibility with the original Arabic-only config
while also importing from the new modular configuration in src/config/.

For new code, prefer importing directly from src.config:
    from src.config import DATASETS, FILTER_CONFIGS, MINHASH_CONFIG
"""
from pathlib import Path
import os

# =============================================================================
# Import from new modular config (preferred)
# =============================================================================
from src.config.common import (
    BASE_DIR,
    DATA_DIR,
    DOWNLOADS_DIR,
    LOGS_DIR,
    MINHASH_CONFIG,
    NUM_WORKERS,
    BATCH_SIZE,
)
from src.config.datasets_ar import DATASETS_AR
from src.config.datasets_tr import DATASETS_TR
from src.config.datasets_hi import DATASETS_HI
from src.config.filter_thresholds import (
    AR_FILTER_CONFIG,
    TR_FILTER_CONFIG,
    HI_FILTER_CONFIG,
)

# =============================================================================
# Backward Compatibility: Original Arabic Config Names
# =============================================================================
# These aliases maintain compatibility with existing code

# DATASETS refers to Arabic datasets by default (original behavior)
DATASETS = DATASETS_AR

# Arabic filter config with original name
ARABIC_FILTER_CONFIG = AR_FILTER_CONFIG

# Original NUM_TASKS variable (now derived from CPU count)
NUM_TASKS = NUM_WORKERS

# =============================================================================
# Multi-Language Dataset Access
# =============================================================================
# Use these for new multi-language code
DATASETS_BY_LANGUAGE = {
    "ar": DATASETS_AR,
    "tr": DATASETS_TR,
    "hi": DATASETS_HI,
}

FILTER_CONFIGS = {
    "ar": AR_FILTER_CONFIG,
    "tr": TR_FILTER_CONFIG,
    "hi": HI_FILTER_CONFIG,
}

# =============================================================================
# Sentence Deduplication Configuration
# =============================================================================
# Note: Not used for Turkish/Hindi (per user request)
SENTENCE_DEDUP_CONFIG = {
    "n_sentences": 3,           # Match 3-sentence spans
    "min_sentence_words": 5,    # Minimum words per sentence
    "min_doc_words_after": 50,  # Minimum words after deduplication
    "min_duplicate_count": 3,   # Remove spans appearing 3+ times
}

# =============================================================================
# Final Dataset Statistics (AraMix)
# =============================================================================
# These are the final statistics after all processing
FINAL_STATS = {
    "minhash_deduped": {
        "documents": 178_883_241,
        "words": 78_509_333_052,
    },
    "consensus": {
        "documents": 47_900_000,  # Documents appearing in 2+ datasets
    },
    "sentence_deduped": {
        "documents": 167_571_677,
        "words": 71_830_479_875,
        "tokens": 158_842_639_843,  # Llama-3.2-3B tokenizer
        "by_source": {
            "uonlp/CulturaX": {"tokens": 38_397_662_500, "docs": 40_833_224},
            "lightonai/ArabicWeb24": {"tokens": 31_581_741_093, "docs": 33_582_431},
            "HPLT/HPLT2.0_cleaned": {"tokens": 30_379_929_944, "docs": 33_058_401},
            "HuggingFaceFW/fineweb-2": {"tokens": 24_190_368_212, "docs": 30_639_764},
            "allenai/c4": {"tokens": 20_446_939_204, "docs": 22_957_289},
            "ClusterlabAi/101_billion_arabic_words_dataset": {"tokens": 7_749_774_915, "docs": 5_852_369},
            "HuggingFaceFW/finepdfs": {"tokens": 6_096_223_975, "docs": 648_199},
        },
    },
    "sentence_dedup_removal": {
        "docs_removed": 11_311_564,
        "words_removed": 6_340_127_945,
        "sentences_removed": 401_569_864,
    },
}
