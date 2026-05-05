"""
Italian Quality Filter for Web Text Data.

This filter extends the base quality filter with Italian-specific configurations.
Italian uses the Latin script with accented vowels (à, è, é, ì, ò, ù).
"""
import re
from typing import Pattern

from datatrove.pipeline.writers.disk_base import DiskWriter

from .base_quality import QualityFilterBase
from .lang_config import (
    ITALIAN_SCRIPT_RANGE,
    ITALIAN_SPECIFIC_CHARS,
    ITALIAN_TERMINAL_PUNCTUATION,
    ITALIAN_POLICY_PHRASES,
    ITALIAN_PLACEHOLDER_PATTERNS,
    ITALIAN_CITATION_REGEX,
    ITALIAN_REPETITION_PATTERNS,
)


class ItQualityFilter(QualityFilterBase):
    """
    Quality filter optimized for Italian web text.

    Italian uses the Latin script with accented vowels:
    - à, À (a with grave)
    - è, È (e with grave)
    - é, É (e with acute)
    - ì, Ì (i with grave)
    - ò, Ò (o with grave)
    - ù, Ù (u with grave)

    This filter checks for the presence of Italian-specific characters
    to ensure the text is actually Italian and not just generic Latin text.
    """
    name = "🇮🇹 Italian Quality"

    def __init__(
        self,
        exclusion_writer: DiskWriter | None = None,
        # Italian-specific default thresholds (similar to Fineweb-2 patterns)
        line_punct_thr: float = 0.091,
        line_punct_exclude_zero: bool = False,
        min_doc_length: int = 100,
        min_doc_words: int = 20,
        short_line_thr: float = 0.67,
        short_line_length: int = 30,
        min_words_per_line: int = 2,
        max_word_length: int = 100,
        char_duplicates_ratio: float = 0.1,
        max_char_repetition: int = 5,
        new_line_ratio: float = 0.25,
        max_bullet_ratio: float = 0.9,
        filter_javascript: bool = True,
        filter_curly_bracket: bool = True,
        filter_lorem_ipsum: bool = True,
        filter_policy: bool = True,
        remove_citations: bool = True,
        min_script_ratio: float = 0.65,  # Latin script
        filter_excessive_repetition: bool = True,
        # Italian-specific: minimum ratio of Italian-specific characters
        min_italian_char_ratio: float = 0.005,  # At least 0.5% Italian-specific chars
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
        self.min_italian_char_ratio = min_italian_char_ratio

    @property
    def script_range(self) -> Pattern:
        return ITALIAN_SCRIPT_RANGE

    @property
    def terminal_punctuation(self) -> tuple[str, ...]:
        return ITALIAN_TERMINAL_PUNCTUATION

    @property
    def policy_phrases(self) -> list[str]:
        return ITALIAN_POLICY_PHRASES

    @property
    def placeholder_patterns(self) -> list[str]:
        return ITALIAN_PLACEHOLDER_PATTERNS

    @property
    def citation_regex(self) -> Pattern:
        return ITALIAN_CITATION_REGEX

    @property
    def repetition_patterns(self) -> Pattern:
        return ITALIAN_REPETITION_PATTERNS

    def _count_italian_specific_chars(self, text: str) -> int:
        """Count Italian-specific characters (accented vowels)."""
        return len(ITALIAN_SPECIFIC_CHARS.findall(text))

    def filter(self, doc) -> bool | tuple[bool, str]:
        """
        Filter with additional Italian-specific checks.

        In addition to the base filter checks, we verify that the text
        contains Italian-specific characters to distinguish from other
        Latin-script languages.
        """
        text = doc.text

        # Check for Italian-specific characters
        # This helps distinguish Italian from other Latin-script languages
        alpha_count = self._count_alpha_chars(text)
        if alpha_count > 0:
            italian_char_count = self._count_italian_specific_chars(text)
            italian_ratio = italian_char_count / alpha_count
            if italian_ratio < self.min_italian_char_ratio:
                self.stat_update("low_italian_char_ratio")
                return False, "low_italian_char_ratio"

        # Run the base filter
        return super().filter(doc)


# Backward compatibility alias
ItalianQualityFilter = ItQualityFilter
