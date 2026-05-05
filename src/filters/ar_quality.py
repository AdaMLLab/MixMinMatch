"""
Comprehensive Arabic Quality Filter for Web Text Data.

This filter combines the best approaches from C4, Gopher, and FineWeb,
adapted specifically for Arabic text characteristics:

1. Arabic-aware terminal punctuation (Arabic + Latin)
2. Boilerplate/policy filtering (Arabic + English phrases)
3. Code/template detection (JavaScript, curly brackets)
4. Repetition detection (character-level and line-level)
5. Short line and list detection
6. Language verification (Arabic character ratio)
7. Long word filtering (URLs, encoded garbage)
8. Lorem ipsum and placeholder detection
"""
import re
import unicodedata
from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.filters.gopher_repetition_filter import find_duplicates
from datatrove.pipeline.writers.disk_base import DiskWriter


# =============================================================================
# Arabic Unicode Ranges
# =============================================================================
ARABIC_RANGE = re.compile(
    r'[\u0600-\u06FF'    # Arabic
    r'\u0750-\u077F'     # Arabic Supplement
    r'\u08A0-\u08FF'     # Arabic Extended-A
    r'\uFB50-\uFDFF'     # Arabic Presentation Forms-A
    r'\uFE70-\uFEFF]'    # Arabic Presentation Forms-B
)

# =============================================================================
# Terminal Punctuation (Arabic + Latin + Unicode)
# =============================================================================
ARABIC_TERMINAL_PUNCTUATION = (
    # Latin punctuation (commonly used in modern Arabic web text)
    '.', '!', '?', '"', "'",
    # Arabic-specific punctuation
    '\u061F',  # ؟ Arabic question mark
    '\u06D4',  # ۔ Arabic full stop
    '\u061E',  # ؞ Arabic triple dot punctuation mark
    '\u061D',  # ؝ Arabic end of text mark
    # Common line-ending characters
    ':', ';', ')', ']',
    '\u00BB',  # » Right-pointing double angle quotation mark
    '\u201D',  # " Right double quotation mark
    '\u2019',  # ' Right single quotation mark
    '\u300B',  # 》 Right double angle bracket (used in some contexts)
)

# =============================================================================
# Boilerplate/Policy Phrases to Filter
# =============================================================================
# English policy phrases (from C4)
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

# Arabic policy/boilerplate phrases
ARABIC_POLICY_SUBSTRINGS = [
    "سياسة الخصوصية",           # privacy policy
    "شروط الاستخدام",           # terms of use
    "شروط الخدمة",              # terms of service
    "سياسة ملفات تعريف الارتباط",  # cookie policy
    "ملفات تعريف الارتباط",      # cookies
    "نستخدم ملفات تعريف الارتباط",  # we use cookies
    "جميع الحقوق محفوظة",        # all rights reserved
    "حقوق الطبع والنشر",         # copyright
    "حقوق النشر محفوظة",         # copyright reserved
    "اشترك في النشرة الإخبارية",  # subscribe to newsletter
    "سجل في النشرة",            # sign up for newsletter
    "للاشتراك في القائمة البريدية",  # to subscribe to mailing list
    "أدخل بريدك الإلكتروني",     # enter your email
    "تسجيل الدخول",             # login
    "إنشاء حساب",               # create account
    "هل نسيت كلمة المرور",       # forgot password
    "تابعنا على",               # follow us on
    "شاركنا على",               # share on
    "اقرأ المزيد",              # read more (often boilerplate)
    "المزيد من المقالات",        # more articles
    "مقالات ذات صلة",           # related articles
    "التعليقات مغلقة",          # comments closed
    "اترك تعليقا",              # leave a comment
]

ALL_POLICY_SUBSTRINGS = ENGLISH_POLICY_SUBSTRINGS + ARABIC_POLICY_SUBSTRINGS

# =============================================================================
# Placeholder/Lorem Ipsum Detection
# =============================================================================
PLACEHOLDER_PATTERNS = [
    "lorem ipsum",
    "dolor sit amet",
    "consectetur adipiscing",
    # Arabic placeholder text (less common but exists)
    "هذا النص هو مثال",          # this text is an example
    "نص تجريبي",                # test text
    "هذا نص وهمي",              # this is dummy text
]

# =============================================================================
# Citation/Edit Markers (Wikipedia-style)
# =============================================================================
CITATION_REGEX = re.compile(r'\[\d+\]|\[edit\]|\[citation needed\]|\[بحاجة لمصدر\]|\[تحرير\]')

# =============================================================================
# Excessive Repetition Patterns
# =============================================================================
# Matches 4+ consecutive identical characters (هههههه, !!!!!!, ......, etc.)
CHAR_REPETITION_REGEX = re.compile(r'(.)\1{3,}')

# Matches common Arabic laugh/expression patterns
ARABIC_REPETITION_PATTERNS = re.compile(
    r'[هخخ]{4,}|'       # هههه or خخخخ (laughter)
    r'[اآ]{4,}|'        # آآآآ (exclamation)
    r'[و]{4,}|'         # وووو (exclamation)
    r'[ي]{4,}'          # يييي (exclamation)
)


class ArabicQualityFilter(BaseFilter):
    """
    Comprehensive quality filter optimized for Arabic web text.

    Combines approaches from C4, Gopher, and FineWeb with Arabic-specific adaptations.

    Key features:
    1. Arabic-aware terminal punctuation checking
    2. Boilerplate/policy phrase filtering (Arabic + English)
    3. Code/template detection (curly brackets, JavaScript)
    4. Character and line-level repetition detection
    5. Short line and list/menu detection
    6. Language verification (Arabic character ratio)
    7. Long word filtering (URLs, encoded data)
    8. Minimum document quality thresholds
    """
    name = "🌙 Arabic Quality"

    def __init__(
        self,
        exclusion_writer: DiskWriter | None = None,

        # === Terminal Punctuation Settings ===
        line_punct_thr: float = 0.05,  # 5% of lines should end with punctuation
        line_punct_exclude_zero: bool = True,  # Allow docs with 0% (common in Arabic)
        stop_chars: tuple[str, ...] | None = None,

        # === Document Length Settings ===
        min_doc_length: int = 100,  # Minimum characters
        min_doc_words: int = 20,    # Minimum words

        # === Line Quality Settings ===
        short_line_thr: float = 0.67,  # Max ratio of short lines
        short_line_length: int = 30,   # Definition of "short"
        min_words_per_line: int = 2,   # Filter navigation-style lines
        max_word_length: int = 100,    # Filter lines with URL-like garbage

        # === Repetition/Duplicate Settings ===
        char_duplicates_ratio: float = 0.01,  # Max duplicate character ratio
        max_char_repetition: int = 5,  # Max consecutive identical chars allowed

        # === List/Menu Detection ===
        new_line_ratio: float = 0.5,  # Max newlines per word
        max_bullet_ratio: float = 0.9,  # Max ratio of bullet-starting lines

        # === Content Filtering ===
        filter_javascript: bool = True,
        filter_curly_bracket: bool = True,
        filter_lorem_ipsum: bool = True,
        filter_policy: bool = True,
        remove_citations: bool = True,

        # === Arabic-Specific Settings ===
        min_arabic_ratio: float = 0.3,  # At least 30% Arabic among alphabetic
        filter_excessive_repetition: bool = True,
    ):
        super().__init__(exclusion_writer)

        # Punctuation
        self.line_punct_thr = line_punct_thr
        self.line_punct_exclude_zero = line_punct_exclude_zero
        self.stop_chars = stop_chars if stop_chars is not None else ARABIC_TERMINAL_PUNCTUATION

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

        # Arabic-specific
        self.min_arabic_ratio = min_arabic_ratio
        self.filter_excessive_repetition = filter_excessive_repetition

    def _count_arabic_chars(self, text: str) -> int:
        """Count Arabic script characters in text."""
        return len(ARABIC_RANGE.findall(text))

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

        # Check for Arabic-specific excessive repetition patterns
        if ARABIC_REPETITION_PATTERNS.search(text):
            return True

        return False

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
            for pattern in PLACEHOLDER_PATTERNS:
                if pattern in text_lower:
                    self.stat_update("lorem_ipsum")
                    return False, "lorem_ipsum"

        # Check Arabic character ratio
        alpha_count = self._count_alpha_chars(text)
        if alpha_count > 0:
            arabic_count = self._count_arabic_chars(text)
            arabic_ratio = arabic_count / alpha_count
            if arabic_ratio < self.min_arabic_ratio:
                self.stat_update("low_arabic_ratio")
                return False, "low_arabic_ratio"
        else:
            # No alphabetic characters at all
            self.stat_update("no_alpha_chars")
            return False, "no_alpha_chars"

        # =================================================================
        # Line-Level Processing
        # =================================================================

        # Remove citations if requested
        if self.remove_citations:
            text = CITATION_REGEX.sub('', text)

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
                if any(policy in line_lower for policy in ALL_POLICY_SUBSTRINGS):
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

        # Excessive character repetition (هههههه, !!!!!, etc.)
        if self.filter_excessive_repetition:
            if self._has_excessive_repetition(filtered_text):
                self.stat_update("excessive_repetition")
                return False, "excessive_repetition"

        # =================================================================
        # Update document text with filtered content
        # =================================================================
        doc.text = filtered_text

        return True


# =============================================================================
# Default Configuration
# =============================================================================
ARABIC_FILTER_CONFIG = {
    # Terminal punctuation (lenient for Arabic)
    "line_punct_thr": 0.05,
    "line_punct_exclude_zero": True,

    # Document length
    "min_doc_length": 100,
    "min_doc_words": 20,

    # Line quality
    "short_line_thr": 0.67,
    "short_line_length": 30,
    "min_words_per_line": 2,
    "max_word_length": 100,

    # Repetition
    "char_duplicates_ratio": 0.01,
    "max_char_repetition": 5,

    # List detection
    "new_line_ratio": 0.5,
    "max_bullet_ratio": 0.9,

    # Content filtering
    "filter_javascript": True,
    "filter_curly_bracket": True,
    "filter_lorem_ipsum": True,
    "filter_policy": True,
    "remove_citations": True,

    # Arabic-specific
    "min_arabic_ratio": 0.3,
    "filter_excessive_repetition": True,
}


# =============================================================================
# Lenient Configuration (for initial filtering, stricter dedup later)
# =============================================================================
ARABIC_FILTER_LENIENT = {
    # More lenient punctuation
    "line_punct_thr": 0.0,
    "line_punct_exclude_zero": True,

    # Document length
    "min_doc_length": 50,
    "min_doc_words": 10,

    # Line quality (more lenient)
    "short_line_thr": 0.75,
    "short_line_length": 25,
    "min_words_per_line": 1,
    "max_word_length": 150,

    # Repetition
    "char_duplicates_ratio": 0.02,
    "max_char_repetition": 6,

    # List detection (more lenient)
    "new_line_ratio": 0.6,
    "max_bullet_ratio": 0.95,

    # Content filtering (keep essential)
    "filter_javascript": True,
    "filter_curly_bracket": True,
    "filter_lorem_ipsum": True,
    "filter_policy": False,  # Might filter legitimate content
    "remove_citations": False,

    # Arabic-specific
    "min_arabic_ratio": 0.2,
    "filter_excessive_repetition": True,
}
