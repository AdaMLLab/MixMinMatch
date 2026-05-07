# Multi-Language Pretraining Data Pipeline

A modular pipeline for creating high-quality pretraining data by combining, filtering, and deduplicating web datasets across multiple languages.

## Supported Languages

| Language | Code | Datasets | HuggingFace |
|----------|------|----------|-------------|
| Arabic | `ar` | HPLT2, CulturaX, ArabicWeb24, Clusterlab, C4, FineWeb-2, FinePDFs | [`AdaMLLab/AraMix`](https://huggingface.co/datasets/AdaMLLab/AraMix) |
| Turkish | `tr` | HPLT2, CulturaX, C4, FineWeb-2, VNGRS | [`AdaMLLab/TurMix`](https://huggingface.co/datasets/AdaMLLab/TurMix) |
| Hindi | `hi` | HPLT2, CulturaX, C4, FineWeb-2, Sangraha | [`AdaMLLab/HinMix`](https://huggingface.co/datasets/AdaMLLab/HinMix) |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Full pipeline for Turkish
python run_pipeline.py --language tr --stage all

# Or run individual stages
python run_pipeline.py --language hi --stage download
python run_pipeline.py --language hi --stage filter
python run_pipeline.py --language hi --stage minhash
python scripts/run_consensus.py --language hi
```

## Output Schema

All outputs use a standardized schema with three columns:

### Standard Schema (per-source data)
```
text: str      - Document text content
id: str        - 12-character MD5 hash of normalized text
source: str    - Source dataset name (e.g., "hplt2", "culturax")
```

### Consensus Schema (multi-source overlap)
```
text: str          - Document text content
id: str            - 12-character MD5 hash of normalized text
source: list[str]  - List of source dataset names (e.g., ["c4", "culturax"])
```

**Note:** The `id` column is a short hash of the normalized text content, not a URL or path.

## Pipeline Stages

### 1. Download
Downloads datasets from HuggingFace with language-specific filters.

```bash
python run_pipeline.py --language tr --stage download
```

### 2. Quality Filter
Applies language-specific quality filtering including:
- Script ratio (ensuring target language content)
- Boilerplate/policy phrase removal
- Line quality checks (short lines, punctuation)
- Repetition detection (language-specific patterns)
- N-gram frequency filtering

```bash
python run_pipeline.py --language tr --stage filter
```

### 3. MinHash Deduplication
Removes near-duplicate documents using LSH-based MinHash deduplication.

```bash
python run_pipeline.py --language tr --stage minhash
```

Configuration (in `src/config/common.py`):
```python
MINHASH_CONFIG = {
    "n_grams": 5,              # 5-gram shingles
    "num_buckets": 14,         # LSH buckets
    "hashes_per_bucket": 8,    # Total: 14 * 8 = 112 hashes
    "similarity_threshold": 0.8,
}
```

### 4. Consensus Building
Extracts documents appearing in 2+ sources (high-confidence content).

```bash
python scripts/run_consensus.py --language tr
python scripts/run_consensus.py --language hi --min-sources 3
```

## Token Counting

Token counts are tracked at each pipeline stage using the `meta-llama/Llama-3.2-3B` tokenizer.

```bash
# Count tokens for a specific stage/source
python scripts/run_token_count.py --language tr --stage filtered --source hplt2

# Count tokens for all sources at a stage
python scripts/run_token_count.py --language tr --stage filtered

# Print summary of all logged stats
python scripts/run_token_count.py --summary
```

Results are saved to `data/token_stats.json`.

## Pairwise Overlap Analysis

Analyze document overlap between data sources to understand shared content.

```bash
# Analyze all pairs with token counting (default)
python scripts/run_overlap_analysis.py --language tr

# Analyze specific pairs
python scripts/run_overlap_analysis.py --language hi --pairs "fineweb2,culturax;hplt2,c4"

# Analyze deduped data instead of filtered
python scripts/run_overlap_analysis.py --language tr --stage deduped

# Skip token counting for faster analysis
python scripts/run_overlap_analysis.py --language tr --no-count-tokens
```

Output includes:
- Per-source document and token counts
- Pairwise overlap counts (documents and tokens)
- Overlap percentages relative to each source

Results are saved to `data/{language}/overlap_analysis_{stage}.json`.

## Parquet File Configuration

Output files are configured for HuggingFace Datasets compatibility:

```python
PARQUET_CONFIG = {
    "max_files_per_subset": 200,      # Max 200 files per subset
    "row_group_size": 128 * 1024 * 1024,  # ~128MB row groups
    "write_page_index": True,         # Enable random access
    "compression": "zstd",            # Efficient compression
}
```

### Consolidating Files

If you have too many small parquet files, consolidate them:

```bash
# Consolidate a specific directory
python scripts/consolidate_parquet.py --input data/tr/deduped/hplt2 --output data/tr/deduped_consolidated/hplt2

# Consolidate all sources for a language/stage
python scripts/consolidate_parquet.py --language tr --stage deduped --in-place
```

## Directory Structure

```
arabic-pretraining-mix-other-languages/
├── run_pipeline.py              # Main CLI entry point
├── scripts/
│   ├── run_token_count.py       # Token counting utility
│   ├── run_consensus.py         # Consensus building
│   ├── run_overlap_analysis.py  # Pairwise overlap analysis
│   └── consolidate_parquet.py   # Parquet file consolidation
├── src/
│   ├── config/
│   │   ├── common.py            # MINHASH_CONFIG, PARQUET_CONFIG, NUM_WORKERS
│   │   ├── schema.py            # STANDARD_SCHEMA, CONSENSUS_SCHEMA
│   │   ├── datasets_*.py        # Per-language dataset definitions
│   │   └── filter_thresholds.py # Per-language filter configs
│   ├── filters/
│   │   ├── base_quality.py      # Base filter class
│   │   ├── ar_quality.py        # Arabic filter
│   │   ├── tr_quality.py        # Turkish filter
│   │   └── hi_quality.py        # Hindi filter
│   ├── dedup/
│   │   ├── __init__.py          # MinHash components
│   │   ├── consensus.py         # Consensus builder
│   │   └── overlap_analysis.py  # Pairwise overlap analysis
│   ├── tokenization/
│   │   ├── counter.py           # Parallel token counting
│   │   └── stats.py             # Token stats logging
│   └── writers/
│       └── schema_writer.py     # Schema-enforcing writer
└── data/
    ├── {language}/
    │   ├── downloads/           # Raw downloaded data
    │   ├── filtered/            # Quality-filtered data
    │   ├── deduped/             # MinHash-deduped data
    │   └── consensus/           # Consensus subset
    └── token_stats.json         # Token count log
```

## Language-Specific Quality Filters

### Arabic (`ar_quality.py`)
- Arabic script ratio: min 30%
- Terminal punctuation: Arabic (؟ ۔) + Latin (. ! ?)
- Policy phrases: Arabic + English boilerplate
- Repetition patterns: هههه, خخخخ, آآآآ

### Turkish (`tr_quality.py`)
- Turkish script ratio: min 65% (Latin with Turkish chars ğĞıİöÖüÜşŞçÇ)
- Terminal punctuation: Standard Latin (. ! ? ; :)
- Policy phrases: Turkish boilerplate (gizlilik politikası, çerez politikası, etc.)
- Repetition patterns: jsjsjs, kdkdkd, hahaha

### Hindi (`hi_quality.py`)
- Devanagari script ratio: min 50%
- Terminal punctuation: Devanagari danda (।) + Latin (. ! ?)
- Policy phrases: Hindi boilerplate (गोपनीयता नीति, सेवा की शर्तें, etc.)
- Repetition patterns: हहहह, अअअअ, आआआआ

## Configuration

### Filter Thresholds (per language)

See `src/config/filter_thresholds.py` for complete configs. Example for Turkish:

```python
TR_FILTER_CONFIG = {
    "min_script_ratio": 0.65,
    "lang_score_threshold": 0.875,
    "dup_line_frac": 0.272,
    "new_line_ratio": 0.222,
    "min_avg_word_length": 3,
    "max_avg_word_length": 21,
    "line_punct_thr": 0.091,
    "non_alpha_words_ratio": 0.773,
    "top_5_gram_frac": 0.154,
    "top_10_gram_frac": 0.103,
}
```

### CPU Management

The pipeline reserves 2 CPU cores for system stability:

```python
NUM_WORKERS = max(1, os.cpu_count() - 2)
```

## Requirements

```
datatrove>=0.2.0
datasets>=2.14.0
huggingface_hub>=0.16.0
pyarrow>=12.0.0
transformers>=4.30.0  # For tokenization
```

## AraMix Dataset Statistics

The Arabic dataset is available on HuggingFace: [`SultanR/AraMix`](https://huggingface.co/datasets/SultanR/AraMix)

### Subsets

| Subset | Documents | Tokens | Description |
|--------|-----------|--------|-------------|
| **minhash_deduped** | 178.9M | - | MinHash-deduplicated from 7 sources |
| **consensus** | 47.9M | 54.1B | Documents in 2+ sources |
| **sentence_deduped** | 167.6M | 158.8B | Sentence-level deduplicated |

### Token Counts by Source (sentence_deduped)

| Source | Tokens | Documents |
|--------|--------|-----------|
| CulturaX | 38.4B | 40.8M |
| ArabicWeb24 | 31.6B | 33.6M |
| HPLT 2.0 | 30.4B | 33.1M |
| FineWeb-2 | 24.2B | 30.6M |
| C4 | 20.4B | 23.0M |
| ClusterLab 101B | 7.7B | 5.9M |
| FinePDFs | 6.1B | 648K |
| **Total** | **158.8B** | **167.6M** |

## License

See individual dataset licenses on HuggingFace.
