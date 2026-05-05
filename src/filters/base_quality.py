"""
Base Quality Filter for Web Text Data.

This module provides a language-agnostic base class for quality filtering.
Language-specific filters inherit from this class and override the
language-specific properties.
"""
import re
import unicodedata
from abc import abstractmethod
from typing import Pattern

from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.filters.gopher_repetition_filter import find_duplicates
from datatrove.pipeline.writers.disk_base import DiskWriter


# =============================================================================
# Common Constants
# =============================================================================
# Matches 4+ consecutive identical characters
CHAR_REPETITION_REGEX = re.compile(r'(.)\1{3,}')

# Common English policy phrases (shared across all languages)
ENGLISH_POLICY_SUBSTRINGS = [
    "terms of use",
    "terms of service",
    "privacy policy",
    "cookie policy",
    "uses cookies",
    "use of cookies",
    "use cookies",
    "accept cookies",
    "cookie settings",
    "gdpr",
    "all rights reserved",
    "copyright ©",
    "subscribe to our newsletter",
    "sign up for our newsletter",
]

# Common placeholder patterns (shared)
COMMON_PLACEHOLDER_PATTERNS = [
    "lorem ipsum",
    "dolor sit amet",
    "consectetur adipiscing",
]

# Common citation patterns
COMMON_CITATION_REGEX = re.compile(r'\[\d+\]|\[edit\]|\[citation needed\]')


class QualityFilterBase(BaseFilter):
    """
    Base quality filter for web text data.

    This class provides the common filtering logic shared across all languages.
    Language-specific filters should inherit from this class and override
    the abstract properties to provide language-specific configurations.

    Key features:
    1. Script-aware character ratio checking
    2. Boilerplate/policy phrase filtering (target language + English)
    3. Code/template detection (curly brackets, JavaScript)
    4. Character and line-level repetition detection
    5. Short line and list/menu detection
    6. Long word filtering (URLs, encoded data)
    7. Minimum document quality thresholds
    """

    def __init__(
        self,
        exclusion_writer: DiskWriter | None = None,

        # === Terminal Punctuation Settings ===
        line_punct_thr: float = 0.05,
        line_punct_exclude_zero: bool = True,
        stop_chars: tuple[str, ...] | None = None,

        # === Document Length Settings ===
        min_doc_length: int = 100,
        min_doc_words: int = 20,

        # === Line Quality Settings ===
        short_line_thr: float = 0.67,
        short_line_length: int = 30,
        min_words_per_line: int = 2,
        max_word_length: int = 100,

        # === Repetition/Duplicate Settings ===
        char_duplicates_ratio: float = 0.01,
        max_char_repetition: int = 5,

        # === List/Menu Detection ===
        new_line_ratio: float = 0.5,
        max_bullet_ratio: float = 0.9,

        # === Content Filtering ===
        filter_javascript: bool = True,
        filter_curly_bracket: bool = True,
        filter_lorem_ipsum: bool = True,
        filter_policy: bool = True,
        remove_citations: bool = True,

        # === Script-Specific Settings ===
        min_script_ratio: float = 0.3,
        filter_excessive_repetition: bool = True,
    ):
        super().__init__(exclusion_writer)

        # Punctuation
        self.line_punct_thr = line_punct_thr
        self.line_punct_exclude_zero = line_punct_exclude_zero
        self._stop_chars = stop_chars

        # Document length
        self.min_doc_length = min_doc_length
        self.min_doc_words = min_doc_words

        # Line quality
        self.short_line_thr = short_line_thr
        self.short_line_length = short_line_length
        self.min_words_per_line = min_words_per_line
        self.max_word_length = max_word_length

        # Repetition
        self.char_duplicates_ratio = char_duplicates_ratio
        self.max_char_repetition = max_char_repetition

        # List detection
        self.new_line_ratio = new_line_ratio
        self.max_bullet_ratio = max_bullet_ratio

        # Content filtering
        self.filter_javascript = filter_javascript
        self.filter_curly_bracket = filter_curly_bracket
        self.filter_lorem_ipsum = filter_lorem_ipsum
        self.filter_policy = filter_policy
        self.remove_citations = remove_citations

        # Script-specific
        self.min_script_ratio = min_script_ratio
        self.filter_excessive_repetition = filter_excessive_repetition

    # =========================================================================
    # Abstract Properties - Must be overridden by subclasses
    # =========================================================================

    @property
    @abstractmethod
    def script_range(self) -> Pattern:
        """Compiled regex pattern for detecting target script characters."""
        pass

    @property
    @abstractmethod
    def terminal_punctuation(self) -> tuple[str, ...]:
        """Tuple of characters that are valid line-ending punctuation."""
        pass

    @property
    @abstractmethod
    def policy_phrases(self) -> list[str]:
        """List of language-specific policy/boilerplate phrases to filter."""
        pass

    @property
    @abstractmethod
    def placeholder_patterns(self) -> list[str]:
        """List of language-specific placeholder/lorem ipsum patterns."""
        pass

    @property
    @abstractmethod
    def citation_regex(self) -> Pattern:
        """Compiled regex for detecting citations/edit markers."""
        pass

    @property
    @abstractmethod
    def repetition_patterns(self) -> Pattern | None:
        """Compiled regex for language-specific excessive repetition, or None."""
        pass

    # =========================================================================
    # Computed Properties
    # =========================================================================

    @property
    def stop_chars(self) -> tuple[str, ...]:
        """Get terminal punctuation chars (override or use default)."""
        if self._stop_chars is not None:
            return self._stop_chars
        return self.terminal_punctuation

    @property
    def all_policy_phrases(self) -> list[str]:
        """Combined English + language-specific policy phrases."""
        return ENGLISH_POLICY_SUBSTRINGS + self.policy_phrases

    @property
    def all_placeholder_patterns(self) -> list[str]:
        """Combined common + language-specific placeholder patterns."""
        return COMMON_PLACEHOLDER_PATTERNS + self.placeholder_patterns

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _count_script_chars(self, text: str) -> int:
        """Count characters in the target script."""
        return len(self.script_range.findall(text))

    def _count_alpha_chars(self, text: str) -> int:
        """Count all alphabetic characters (any script)."""
        return sum(1 for c in text if unicodedata.category(c).startswith('L'))

    def _has_excessive_repetition(self, text: str) -> bool:
        """Check for excessive character repetition."""
        # Check for any character repeated more than max_char_repetition times
        for match in CHAR_REPETITION_REGEX.finditer(text):
            if len(match.group(0)) > self.max_char_repetition:
                # Allow some exceptions for ellipsis and common patterns
                char = match.group(1)
                if char not in '.…-_=':
                    return True

        # Check for language-specific excessive repetition patterns
        if self.repetition_patterns is not None:
            if self.repetition_patterns.search(text):
                return True

        return False

    # =========================================================================
    # Main Filter Logic
    # =========================================================================

    def filter(self, doc) -> bool | tuple[bool, str]:
        text = doc.text
        text_lower = text.lower()

        # =================================================================
        # Document-Level Checks (reject entire document)
        # =================================================================

        # Check minimum document length (characters)
        if len(text) < self.min_doc_length:
            self.stat_update("doc_too_short_chars")
            return False, "too_short_chars"

        # Check for curly brackets (code/templates)
        if self.filter_curly_bracket and '{' in text:
            self.stat_update("curly_bracket")
            return False, "curly_bracket"

        # Check for lorem ipsum / placeholder text
        if self.filter_lorem_ipsum:
            for pattern in self.all_placeholder_patterns:
                if pattern in text_lower:
                    self.stat_update("lorem_ipsum")
                    return False, "lorem_ipsum"

        # Check script character ratio
        alpha_count = self._count_alpha_chars(text)
        if alpha_count > 0:
            script_count = self._count_script_chars(text)
            script_ratio = script_count / alpha_count
            if script_ratio < self.min_script_ratio:
                self.stat_update("low_script_ratio")
                return False, "low_script_ratio"
        else:
            # No alphabetic characters at all
            self.stat_update("no_alpha_chars")
            return False, "no_alpha_chars"

        # =================================================================
        # Line-Level Processing
        # =================================================================

        # Remove citations if requested
        if self.remove_citations:
            text = self.citation_regex.sub('', text)

        # Split into lines and process
        lines = text.split('\n')
        kept_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            words = line.split()
            line_lower = line.lower()

            # Skip lines with very long words (URLs, encoded data)
            if self.max_word_length > 0:
                if any(len(word) > self.max_word_length for word in words):
                    self.stat_update("line_long_word")
                    continue

            # Skip lines mentioning JavaScript
            if self.filter_javascript and 'javascript' in line_lower:
                self.stat_update("line_javascript")
                continue

            # Skip policy/boilerplate lines
            if self.filter_policy:
                if any(policy in line_lower for policy in self.all_policy_phrases):
                    self.stat_update("line_policy")
                    continue

            # Skip lines with too few words (navigation menus, etc.)
            if self.min_words_per_line > 0 and len(words) < self.min_words_per_line:
                # But keep lines that end with terminal punctuation (might be short sentences)
                if not line.rstrip().endswith(self.stop_chars):
                    self.stat_update("line_too_few_words")
                    continue

            kept_lines.append(line)

        # Check if we have any lines left
        if len(kept_lines) == 0:
            self.stat_update("empty_after_filtering")
            return False, "empty"

        # Check minimum word count
        total_words = sum(len(line.split()) for line in kept_lines)
        if total_words < self.min_doc_words:
            self.stat_update("doc_too_few_words")
            return False, "too_few_words"

        # =================================================================
        # Line Ratio Checks
        # =================================================================

        # Terminal punctuation ratio
        punct_lines = sum(1 for line in kept_lines if line.rstrip().endswith(self.stop_chars))
        punct_ratio = punct_lines / len(kept_lines)
        if punct_ratio < self.line_punct_thr:
            if not (punct_ratio == 0 and self.line_punct_exclude_zero):
                self.stat_update("low_punct_ratio")
                return False, "line_punct_ratio"

        # Short line ratio
        short_lines = sum(1 for line in kept_lines if len(line) <= self.short_line_length)
        short_ratio = short_lines / len(kept_lines)
        if short_ratio > self.short_line_thr:
            self.stat_update("too_many_short_lines")
            return False, "short_line_ratio"

        # Bullet point ratio (lists/menus)
        bullet_lines = sum(
            1 for line in kept_lines
            if line.lstrip().startswith(('•', '-', '*', '–', '►', '▪', '●'))
        )
        bullet_ratio = bullet_lines / len(kept_lines)
        if bullet_ratio > self.max_bullet_ratio:
            self.stat_update("too_many_bullets")
            return False, "bullet_ratio"

        # Newline ratio (list detection)
        filtered_text = '\n'.join(kept_lines)
        newline_count = filtered_text.count('\n')
        if total_words > 0:
            nl_ratio = newline_count / total_words
            if nl_ratio > self.new_line_ratio:
                self.stat_update("high_newline_ratio")
                return False, "list_ratio"

        # =================================================================
        # Repetition/Duplicate Checks
        # =================================================================

        # Character duplicate ratio (from Gopher/FineWeb)
        text_no_newlines = filtered_text.replace('\n', '')
        if len(text_no_newlines) > 0:
            dup_chars = find_duplicates(kept_lines)[1]
            dup_ratio = dup_chars / len(text_no_newlines)
            if dup_ratio > self.char_duplicates_ratio:
                self.stat_update("high_char_duplicates")
                return False, "char_dup_ratio"

        # Excessive character repetition
        if self.filter_excessive_repetition:
            if self._has_excessive_repetition(filtered_text):
                self.stat_update("excessive_repetition")
                return False, "excessive_repetition"

        # =================================================================
        # Update document text with filtered content
        # =================================================================
        doc.text = filtered_text

        return True
