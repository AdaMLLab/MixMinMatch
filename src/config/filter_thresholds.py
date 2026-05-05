"""Per-language filter threshold configurations.

These thresholds are derived from:
- Arabic: Original AraMix pipeline tuning
- Turkish: Fineweb-2 tur_Latn config + custom tuning
- Hindi: Fineweb-2 hin_Deva config + custom tuning
"""

# =============================================================================
# Arabic Filter Configuration
# =============================================================================
AR_FILTER_CONFIG = {
    # Terminal punctuation (lenient for Arabic)
    "line_punct_thr": 0.05,          # 5% of lines should end with punctuation
    "line_punct_exclude_zero": True, # Allow 0% (common in Arabic)

    # Document length
    "min_doc_length": 100,           # Minimum characters
    "min_doc_words": 20,             # Minimum words

    # Line quality
    "short_line_thr": 0.67,          # Max 67% short lines
    "short_line_length": 30,         # Definition of "short"
    "min_words_per_line": 2,         # Filter navigation-style lines
    "max_word_length": 100,          # Filter lines with URL-like garbage

    # Repetition
    "char_duplicates_ratio": 0.01,   # Max duplicate character ratio
    "max_char_repetition": 5,        # Max consecutive identical chars

    # List detection
    "new_line_ratio": 0.5,           # Max newlines per word
    "max_bullet_ratio": 0.9,         # Max 90% bullet lines

    # Content filtering
    "filter_javascript": True,
    "filter_curly_bracket": True,
    "filter_lorem_ipsum": True,
    "filter_policy": True,
    "remove_citations": True,

    # Arabic-specific
    "min_script_ratio": 0.3,         # Min 30% Arabic characters
    "filter_excessive_repetition": True,
}

# =============================================================================
# Turkish Filter Configuration
# =============================================================================
# Based on Fineweb-2 tur_Latn.yml config
TR_FILTER_CONFIG = {
    # Terminal punctuation
    "line_punct_thr": 0.091,         # From Fineweb-2
    "line_punct_exclude_zero": False,

    # Document length
    "min_doc_length": 100,
    "min_doc_words": 20,

    # Line quality
    "short_line_thr": 0.67,
    "short_line_length": 30,
    "min_words_per_line": 2,
    "max_word_length": 100,

    # Word length bounds (from Fineweb-2)
    "min_avg_word_length": 3,
    "max_avg_word_length": 21,

    # Repetition (from Fineweb-2)
    "char_duplicates_ratio": 0.1,    # Fineweb-2 uses higher threshold
    "max_char_repetition": 5,
    "dup_line_frac": 0.272,          # From Fineweb-2
    "new_line_ratio": 0.222,         # From Fineweb-2

    # N-gram thresholds (from Fineweb-2)
    "top_5_gram_frac": 0.154,
    "top_10_gram_frac": 0.103,

    # Content filtering
    "filter_javascript": True,
    "filter_curly_bracket": True,
    "filter_lorem_ipsum": True,
    "filter_policy": True,
    "remove_citations": True,

    # Turkish uses Latin script
    "min_script_ratio": 0.65,        # Min Latin characters with Turkish chars
    "filter_excessive_repetition": True,

    # Language score (from Fineweb-2)
    "lang_score_threshold": 0.875,
    "non_alpha_words_ratio": 0.773,
}

# =============================================================================
# Hindi Filter Configuration
# =============================================================================
# Based on Fineweb-2 hin_Deva.yml config
HI_FILTER_CONFIG = {
    # Terminal punctuation
    "line_punct_thr": 0.091,         # From Fineweb-2
    "line_punct_exclude_zero": True, # Hindi may have less punctuation

    # Document length
    "min_doc_length": 100,
    "min_doc_words": 20,

    # Line quality
    "short_line_thr": 0.67,
    "short_line_length": 30,
    "min_words_per_line": 2,
    "max_word_length": 100,

    # Word length bounds (from Fineweb-2)
    "min_avg_word_length": 2,        # Hindi words can be shorter
    "max_avg_word_length": 21,

    # Repetition (from Fineweb-2)
    "char_duplicates_ratio": 0.1,
    "max_char_repetition": 5,
    "dup_line_frac": 0.206,          # From Fineweb-2
    "new_line_ratio": 0.316,         # From Fineweb-2

    # N-gram thresholds (from Fineweb-2)
    "top_5_gram_frac": 0.135,
    "top_10_gram_frac": 0.090,

    # Content filtering
    "filter_javascript": True,
    "filter_curly_bracket": True,
    "filter_lorem_ipsum": True,
    "filter_policy": True,
    "remove_citations": True,

    # Hindi uses Devanagari script
    "min_script_ratio": 0.5,         # Lower due to English mixing in Hindi web text
    "filter_excessive_repetition": True,

    # Language score (from Fineweb-2)
    "lang_score_threshold": 0.692,
    "non_alpha_words_ratio": 0.837,
}

# =============================================================================
# Italian Filter Configuration
# =============================================================================
# Based on similar Latin-script language patterns (Turkish)
# Italian uses the same datasets as Hindi (without Sangraha)
IT_FILTER_CONFIG = {
    # Terminal punctuation
    "line_punct_thr": 0.091,
    "line_punct_exclude_zero": False,

    # Document length
    "min_doc_length": 100,
    "min_doc_words": 20,

    # Line quality
    "short_line_thr": 0.67,
    "short_line_length": 30,
    "min_words_per_line": 2,
    "max_word_length": 100,

    # Word length bounds
    "min_avg_word_length": 3,
    "max_avg_word_length": 21,

    # Repetition
    "char_duplicates_ratio": 0.1,
    "max_char_repetition": 5,
    "dup_line_frac": 0.25,
    "new_line_ratio": 0.25,

    # N-gram thresholds
    "top_5_gram_frac": 0.15,
    "top_10_gram_frac": 0.10,

    # Content filtering
    "filter_javascript": True,
    "filter_curly_bracket": True,
    "filter_lorem_ipsum": True,
    "filter_policy": True,
    "remove_citations": True,

    # Italian uses Latin script with accented vowels
    "min_script_ratio": 0.65,
    "filter_excessive_repetition": True,

    # Language detection thresholds
    "lang_score_threshold": 0.85,
    "non_alpha_words_ratio": 0.75,

    # Italian-specific: minimum ratio of accented vowels (à, è, é, ì, ò, ù)
    # Disabled (set to 0) - datasets are already language-filtered to Italian
    # Many Italian web texts omit proper accents, so this check can be overly restrictive
    "min_italian_char_ratio": 0.0,
}

# =============================================================================
# Thai Filter Configuration
# =============================================================================
# Based on Hindi config (similar non-Latin script characteristics)
# Thai has no spaces between words, so word-based thresholds are adjusted
TH_FILTER_CONFIG = {
    # Terminal punctuation (similar to Hindi)
    "line_punct_thr": 0.091,
    "line_punct_exclude_zero": True,  # Thai may have less punctuation

    # Document length
    "min_doc_length": 100,
    "min_doc_words": 20,

    # Line quality
    "short_line_thr": 0.67,
    "short_line_length": 30,
    "min_words_per_line": 2,
    "max_word_length": 100,

    # Word length bounds (similar to Hindi)
    "min_avg_word_length": 2,
    "max_avg_word_length": 21,

    # Repetition (similar to Hindi)
    "char_duplicates_ratio": 0.1,
    "max_char_repetition": 5,
    "dup_line_frac": 0.206,
    "new_line_ratio": 0.316,

    # N-gram thresholds (similar to Hindi)
    "top_5_gram_frac": 0.135,
    "top_10_gram_frac": 0.090,

    # Content filtering
    "filter_javascript": True,
    "filter_curly_bracket": True,
    "filter_lorem_ipsum": True,
    "filter_policy": True,
    "remove_citations": True,

    # Thai uses Thai script
    "min_script_ratio": 0.5,  # Lower due to English mixing in Thai web text
    "filter_excessive_repetition": True,

    # Language score (similar to Hindi)
    "lang_score_threshold": 0.692,
    "non_alpha_words_ratio": 0.837,
}

# Backward compatibility aliases
ARABIC_FILTER_CONFIG = AR_FILTER_CONFIG
TURKISH_FILTER_CONFIG = TR_FILTER_CONFIG
HINDI_FILTER_CONFIG = HI_FILTER_CONFIG
ITALIAN_FILTER_CONFIG = IT_FILTER_CONFIG
THAI_FILTER_CONFIG = TH_FILTER_CONFIG
