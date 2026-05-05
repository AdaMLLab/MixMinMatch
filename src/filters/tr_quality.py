"""
Turkish Quality Filter for Web Text Data.

This filter extends the base quality filter with Turkish-specific configurations.
Turkish uses the Latin script with additional characters (ğ, ı, ş, ç, ö, ü).
"""
import re
from typing import Pattern

from datatrove.pipeline.writers.disk_base import DiskWriter

from .base_quality import QualityFilterBase
from .lang_config import (
    TURKISH_SCRIPT_RANGE,
    TURKISH_SPECIFIC_CHARS,
    TURKISH_TERMINAL_PUNCTUATION,
    TURKISH_POLICY_PHRASES,
    TURKISH_PLACEHOLDER_PATTERNS,
    TURKISH_CITATION_REGEX,
    TURKISH_REPETITION_PATTERNS,
)


class TrQualityFilter(QualityFilterBase):
    """
    Quality filter optimized for Turkish web text.

    Turkish uses the Latin script with additional characters:
    - ğ, Ğ (g with breve)
    - ı, İ (dotless i, dotted I)
    - ş, Ş (s with cedilla)
    - ç, Ç (c with cedilla)
    - ö, Ö (o with umlaut)
    - ü, Ü (u with umlaut)

    This filter checks for the presence of Turkish-specific characters
    to ensure the text is actually Turkish and not just generic Latin text.
    """
    name = "🇹🇷 Turkish Quality"

    def __init__(
        self,
        exclusion_writer: DiskWriter | None = None,
        # Turkish-specific default thresholds (from Fineweb-2)
        line_punct_thr: float = 0.091,
        line_punct_exclude_zero: bool = False,
        min_doc_length: int = 100,
        min_doc_words: int = 20,
        short_line_thr: float = 0.67,
        short_line_length: int = 30,
        min_words_per_line: int = 2,
        max_word_length: int = 100,
        char_duplicates_ratio: float = 0.1,  # Fineweb-2 uses higher threshold
        max_char_repetition: int = 5,
        new_line_ratio: float = 0.222,  # From Fineweb-2
        max_bullet_ratio: float = 0.9,
        filter_javascript: bool = True,
        filter_curly_bracket: bool = True,
        filter_lorem_ipsum: bool = True,
        filter_policy: bool = True,
        remove_citations: bool = True,
        min_script_ratio: float = 0.65,  # Latin with Turkish chars
        filter_excessive_repetition: bool = True,
        # Turkish-specific: minimum ratio of Turkish-specific characters
        min_turkish_char_ratio: float = 0.01,  # At least 1% Turkish-specific chars
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
        self.min_turkish_char_ratio = min_turkish_char_ratio

    @property
    def script_range(self) -> Pattern:
        return TURKISH_SCRIPT_RANGE

    @property
    def terminal_punctuation(self) -> tuple[str, ...]:
        return TURKISH_TERMINAL_PUNCTUATION

    @property
    def policy_phrases(self) -> list[str]:
        return TURKISH_POLICY_PHRASES

    @property
    def placeholder_patterns(self) -> list[str]:
        return TURKISH_PLACEHOLDER_PATTERNS

    @property
    def citation_regex(self) -> Pattern:
        return TURKISH_CITATION_REGEX

    @property
    def repetition_patterns(self) -> Pattern:
        return TURKISH_REPETITION_PATTERNS

    def _count_turkish_specific_chars(self, text: str) -> int:
        """Count Turkish-specific characters (ğ, ı, ş, ç, ö, ü)."""
        return len(TURKISH_SPECIFIC_CHARS.findall(text))

    def filter(self, doc) -> bool | tuple[bool, str]:
        """
        Filter with additional Turkish-specific checks.

        In addition to the base filter checks, we verify that the text
        contains Turkish-specific characters to distinguish from other
        Latin-script languages.
        """
        text = doc.text

        # Check for Turkish-specific characters
        # This helps distinguish Turkish from other Latin-script languages
        alpha_count = self._count_alpha_chars(text)
        if alpha_count > 0:
            turkish_char_count = self._count_turkish_specific_chars(text)
            turkish_ratio = turkish_char_count / alpha_count
            if turkish_ratio < self.min_turkish_char_ratio:
                self.stat_update("low_turkish_char_ratio")
                return False, "low_turkish_char_ratio"

        # Run the base filter
        return super().filter(doc)


# Backward compatibility alias
TurkishQualityFilter = TrQualityFilter
