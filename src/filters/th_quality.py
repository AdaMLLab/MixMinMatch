"""
Thai Quality Filter for Web Text Data.

This filter extends the base quality filter with Thai-specific configurations.
Thai uses the Thai script (U+0E00-U+0E7F).
"""
import re
from typing import Pattern

from datatrove.pipeline.writers.disk_base import DiskWriter

from .base_quality import QualityFilterBase
from .lang_config import (
    THAI_SCRIPT_RANGE,
    THAI_TERMINAL_PUNCTUATION,
    THAI_POLICY_PHRASES,
    THAI_PLACEHOLDER_PATTERNS,
    THAI_CITATION_REGEX,
    THAI_REPETITION_PATTERNS,
)


class ThQualityFilter(QualityFilterBase):
    """
    Quality filter optimized for Thai web text.

    Thai uses the Thai script with Unicode range:
    - U+0E00-U+0E7F (Thai block)

    Key characteristics of Thai:
    - No spaces between words (similar to Chinese/Japanese)
    - Uses tone marks and vowel diacritics
    - Often mixed with English words and phrases (code-mixing)
    - "555" is commonly used for laughter (5 = "ha" in Thai)

    The script ratio threshold is set lower due to English mixing.
    """
    name = "Thai Quality"

    def __init__(
        self,
        exclusion_writer: DiskWriter | None = None,
        # Thai-specific default thresholds (similar to Hindi)
        line_punct_thr: float = 0.091,
        line_punct_exclude_zero: bool = True,  # Thai may have less punctuation
        min_doc_length: int = 100,
        min_doc_words: int = 20,
        short_line_thr: float = 0.67,
        short_line_length: int = 30,
        min_words_per_line: int = 2,
        max_word_length: int = 100,
        char_duplicates_ratio: float = 0.1,
        max_char_repetition: int = 5,
        new_line_ratio: float = 0.316,
        max_bullet_ratio: float = 0.9,
        filter_javascript: bool = True,
        filter_curly_bracket: bool = True,
        filter_lorem_ipsum: bool = True,
        filter_policy: bool = True,
        remove_citations: bool = True,
        # Thai has lower script ratio due to English mixing
        min_script_ratio: float = 0.5,
        filter_excessive_repetition: bool = True,
        **kwargs,
    ):
        super().__init__(
            exclusion_writer=exclusion_writer,
            line_punct_thr=line_punct_thr,
            line_punct_exclude_zero=line_punct_exclude_zero,
            min_doc_length=min_doc_length,
            min_doc_words=min_doc_words,
            short_line_thr=short_line_thr,
            short_line_length=short_line_length,
            min_words_per_line=min_words_per_line,
            max_word_length=max_word_length,
            char_duplicates_ratio=char_duplicates_ratio,
            max_char_repetition=max_char_repetition,
            new_line_ratio=new_line_ratio,
            max_bullet_ratio=max_bullet_ratio,
            filter_javascript=filter_javascript,
            filter_curly_bracket=filter_curly_bracket,
            filter_lorem_ipsum=filter_lorem_ipsum,
            filter_policy=filter_policy,
            remove_citations=remove_citations,
            min_script_ratio=min_script_ratio,
            filter_excessive_repetition=filter_excessive_repetition,
        )

    @property
    def script_range(self) -> Pattern:
        return THAI_SCRIPT_RANGE

    @property
    def terminal_punctuation(self) -> tuple[str, ...]:
        return THAI_TERMINAL_PUNCTUATION

    @property
    def policy_phrases(self) -> list[str]:
        return THAI_POLICY_PHRASES

    @property
    def placeholder_patterns(self) -> list[str]:
        return THAI_PLACEHOLDER_PATTERNS

    @property
    def citation_regex(self) -> Pattern:
        return THAI_CITATION_REGEX

    @property
    def repetition_patterns(self) -> Pattern:
        return THAI_REPETITION_PATTERNS


# Backward compatibility alias
ThaiQualityFilter = ThQualityFilter
