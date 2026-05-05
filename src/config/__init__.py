"""Configuration modules for the pretraining data pipeline."""
import os

from .common import (
    BASE_DIR,
    DATA_DIR,
    DOWNLOADS_DIR,
    LOGS_DIR,
    MINHASH_CONFIG,
    PARQUET_CONFIG,
    NUM_WORKERS,
)
from .schema import STANDARD_SCHEMA, CONSENSUS_SCHEMA
from .datasets_ar import DATASETS_AR
from .datasets_tr import DATASETS_TR
from .datasets_hi import DATASETS_HI
from .datasets_it import DATASETS_IT
from .datasets_th import DATASETS_TH
from .filter_thresholds import (
    AR_FILTER_CONFIG,
    TR_FILTER_CONFIG,
    HI_FILTER_CONFIG,
    IT_FILTER_CONFIG,
    TH_FILTER_CONFIG,
)

# Language selector
DATASETS = {
    "ar": DATASETS_AR,
    "tr": DATASETS_TR,
    "hi": DATASETS_HI,
    "it": DATASETS_IT,
    "th": DATASETS_TH,
}

FILTER_CONFIGS = {
    "ar": AR_FILTER_CONFIG,
    "tr": TR_FILTER_CONFIG,
    "hi": HI_FILTER_CONFIG,
    "it": IT_FILTER_CONFIG,
    "th": TH_FILTER_CONFIG,
}

__all__ = [
    # Paths
    "BASE_DIR",
    "DATA_DIR",
    "DOWNLOADS_DIR",
    "LOGS_DIR",
    # Processing configs
    "MINHASH_CONFIG",
    "PARQUET_CONFIG",
    "NUM_WORKERS",
    # Schema definitions
    "STANDARD_SCHEMA",
    "CONSENSUS_SCHEMA",
    # Dataset configs
    "DATASETS_AR",
    "DATASETS_TR",
    "DATASETS_HI",
    "DATASETS_IT",
    "DATASETS_TH",
    "DATASETS",
    # Filter configs
    "AR_FILTER_CONFIG",
    "TR_FILTER_CONFIG",
    "HI_FILTER_CONFIG",
    "IT_FILTER_CONFIG",
    "TH_FILTER_CONFIG",
    "FILTER_CONFIGS",
]
