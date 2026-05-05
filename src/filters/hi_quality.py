"""
Hindi Quality Filter for Web Text Data.

This filter extends the base quality filter with Hindi-specific configurations.
Hindi uses the Devanagari script (U+0900-U+097F).
"""
import re
from typing import Pattern

from datatrove.pipeline.writers.disk_base import DiskWriter

from .base_quality import QualityFilterBase
from .lang_config import (
    HINDI_SCRIPT_RANGE,
    HINDI_TERMINAL_PUNCTUATION,
    HINDI_POLICY_PHRASES,
    HINDI_PLACEHOLDER_PATTERNS,
    HINDI_CITATION_REGEX,
    HINDI_REPETITION_PATTERNS,
)


class HiQualityFilter(QualityFilterBase):
    """
    Quality filter optimized for Hindi web text.

    Hindi uses the Devanagari script with Unicode ranges:
    - U+0900-U+097F (main Devanagari block)
    - U+A8E0-U+A8FF (Devanagari Extended)
    - U+1CD0-U+1CFF (Vedic Extensions)

    Hindi web text often contains English words and phrases (code-mixing),
    so the script ratio threshold is set lower than for Arabic.
    """
    name = "🇮🇳 Hindi Quality"

    def __init__(
        self,
        exclusion_writer: DiskWriter | None = None,
        # Hindi-specific default thresholds (from Fineweb-2)
        line_punct_thr: float = 0.091,
        line_punct_exclude_zero: bool = True,  # Hindi may have less punctuation
        min_doc_length: int = 100,
        min_doc_words: int = 20,
        short_line_thr: float = 0.67,
        short_line_length: int = 30,
        min_words_per_line: int = 2,
        max_word_length: int = 100,
        char_duplicates_ratio: float = 0.1,  # Fineweb-2 uses higher threshold
        max_char_repetition: int = 5,
        new_line_ratio: float = 0.316,  # From Fineweb-2 (higher for Hindi)
        max_bullet_ratio: float = 0.9,
        filter_javascript: bool = True,
        filter_curly_bracket: bool = True,
        filter_lorem_ipsum: bool = True,
        filter_policy: bool = True,
        remove_citations: bool = True,
        # Hindi has lower script ratio due to English mixing
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
        return HINDI_SCRIPT_RANGE

    @property
    def terminal_punctuation(self) -> tuple[str, ...]:
        return HINDI_TERMINAL_PUNCTUATION

    @property
    def policy_phrases(self) -> list[str]:
        return HINDI_POLICY_PHRASES

    @property
    def placeholder_patterns(self) -> list[str]:
        return HINDI_PLACEHOLDER_PATTERNS

    @property
    def citation_regex(self) -> Pattern:
        return HINDI_CITATION_REGEX

    @property
    def repetition_patterns(self) -> Pattern:
        return HINDI_REPETITION_PATTERNS


# Backward compatibility alias
HindiQualityFilter = HiQualityFilter
