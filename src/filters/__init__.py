"""Quality filters for text data."""
# Base class
from .base_quality import QualityFilterBase

# Language-specific filters
from .ar_quality import ArabicQualityFilter, ARABIC_FILTER_CONFIG
from .tr_quality import TrQualityFilter, TurkishQualityFilter
from .hi_quality import HiQualityFilter, HindiQualityFilter
from .it_quality import ItQualityFilter, ItalianQualityFilter
from .th_quality import ThQualityFilter, ThaiQualityFilter

# Language configuration
from .lang_config import LANGUAGE_CONFIG

# Backward compatibility alias
ArQualityFilter = ArabicQualityFilter

__all__ = [
    # Base
    "QualityFilterBase",
    # Arabic
    "ArabicQualityFilter",
    "ArQualityFilter",
    "ARABIC_FILTER_CONFIG",
    # Turkish
    "TrQualityFilter",
    "TurkishQualityFilter",
    # Hindi
    "HiQualityFilter",
    "HindiQualityFilter",
    # Italian
    "ItQualityFilter",
    "ItalianQualityFilter",
    # Thai
    "ThQualityFilter",
    "ThaiQualityFilter",
    # Config
    "LANGUAGE_CONFIG",
]
