"""
High-level download functions for each language.

This module provides convenience functions for downloading all datasets
for a specific language.
"""
import logging
from pathlib import Path
from typing import Optional

from .downloader import download_dataset, get_download_commands

logger = logging.getLogger(__name__)

# Import dataset configurations
try:
    from ..config.datasets_ar import DATASETS_AR
    from ..config.datasets_tr import DATASETS_TR
    from ..config.datasets_hi import DATASETS_HI
    from ..config.datasets_it import DATASETS_IT
    from ..config.datasets_th import DATASETS_TH
    from ..config.common import DATA_DIR
except ImportError:
    # Fallback for direct script execution
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config.datasets_ar import DATASETS_AR
    from src.config.datasets_tr import DATASETS_TR
    from src.config.datasets_hi import DATASETS_HI
    from src.config.datasets_it import DATASETS_IT
    from src.config.datasets_th import DATASETS_TH
    from src.config.common import DATA_DIR


def download_arabic_datasets(
    base_dir: Optional[str | Path] = None,
    dry_run: bool = False,
) -> bool:
    """
    Download all Arabic datasets.

    Args:
        base_dir: Base directory for downloads (default: DATA_DIR)
        dry_run: If True, only print commands without executing

    Returns:
        True if all downloads succeeded (or dry_run), False otherwise
    """
    base_dir = Path(base_dir) if base_dir else DATA_DIR
    language = "ar"

    if dry_run:
        commands = get_download_commands(DATASETS_AR, base_dir, language)
        print(f"\n# Arabic Dataset Download Commands ({len(commands)} datasets)")
        print("# " + "=" * 60)
        for cmd in commands:
            print(cmd)
        return True

    logger.info(f"Downloading {len(DATASETS_AR)} Arabic datasets to {base_dir}")
    success = True
    for config in DATASETS_AR:
        if not download_dataset(config, base_dir, language):
            logger.error(f"Failed to download {config['name']}")
            success = False

    return success


def download_turkish_datasets(
    base_dir: Optional[str | Path] = None,
    dry_run: bool = False,
) -> bool:
    """
    Download all Turkish datasets.

    Args:
        base_dir: Base directory for downloads (default: DATA_DIR)
        dry_run: If True, only print commands without executing

    Returns:
        True if all downloads succeeded (or dry_run), False otherwise
    """
    base_dir = Path(base_dir) if base_dir else DATA_DIR
    language = "tr"

    if dry_run:
        commands = get_download_commands(DATASETS_TR, base_dir, language)
        print(f"\n# Turkish Dataset Download Commands ({len(commands)} datasets)")
        print("# " + "=" * 60)
        for cmd in commands:
            print(cmd)
        return True

    logger.info(f"Downloading {len(DATASETS_TR)} Turkish datasets to {base_dir}")
    success = True
    for config in DATASETS_TR:
        if not download_dataset(config, base_dir, language):
            logger.error(f"Failed to download {config['name']}")
            success = False

    return success


def download_hindi_datasets(
    base_dir: Optional[str | Path] = None,
    dry_run: bool = False,
) -> bool:
    """
    Download all Hindi datasets.

    IMPORTANT: Sangraha dataset requires special handling.
    Hindi is a SPLIT, not a subset. The download function handles this
    automatically by using --include patterns.

    After download, load Sangraha from local files:
        load_dataset("parquet", data_dir="./data/hi/downloads/sangraha_verified")

    Do NOT use:
        load_dataset("ai4bharat/sangraha", ...) # This downloads ALL languages!

    Args:
        base_dir: Base directory for downloads (default: DATA_DIR)
        dry_run: If True, only print commands without executing

    Returns:
        True if all downloads succeeded (or dry_run), False otherwise
    """
    base_dir = Path(base_dir) if base_dir else DATA_DIR
    language = "hi"

    if dry_run:
        commands = get_download_commands(DATASETS_HI, base_dir, language)
        print(f"\n# Hindi Dataset Download Commands ({len(commands)} datasets)")
        print("# " + "=" * 60)
        print("# NOTE: Sangraha downloads use --include to avoid downloading all languages")
        for cmd in commands:
            print(cmd)
        return True

    logger.info(f"Downloading {len(DATASETS_HI)} Hindi datasets to {base_dir}")
    success = True
    for config in DATASETS_HI:
        if not download_dataset(config, base_dir, language):
            logger.error(f"Failed to download {config['name']}")
            success = False

    return success


def download_italian_datasets(
    base_dir: Optional[str | Path] = None,
    dry_run: bool = False,
) -> bool:
    """
    Download all Italian datasets.

    Args:
        base_dir: Base directory for downloads (default: DATA_DIR)
        dry_run: If True, only print commands without executing

    Returns:
        True if all downloads succeeded (or dry_run), False otherwise
    """
    base_dir = Path(base_dir) if base_dir else DATA_DIR
    language = "it"

    if dry_run:
        commands = get_download_commands(DATASETS_IT, base_dir, language)
        print(f"\n# Italian Dataset Download Commands ({len(commands)} datasets)")
        print("# " + "=" * 60)
        for cmd in commands:
            print(cmd)
        return True

    logger.info(f"Downloading {len(DATASETS_IT)} Italian datasets to {base_dir}")
    success = True
    for config in DATASETS_IT:
        if not download_dataset(config, base_dir, language):
            logger.error(f"Failed to download {config['name']}")
            success = False

    return success


def download_thai_datasets(
    base_dir: Optional[str | Path] = None,
    dry_run: bool = False,
) -> bool:
    """
    Download all Thai datasets.

    Args:
        base_dir: Base directory for downloads (default: DATA_DIR)
        dry_run: If True, only print commands without executing

    Returns:
        True if all downloads succeeded (or dry_run), False otherwise
    """
    base_dir = Path(base_dir) if base_dir else DATA_DIR
    language = "th"

    if dry_run:
        commands = get_download_commands(DATASETS_TH, base_dir, language)
        print(f"\n# Thai Dataset Download Commands ({len(commands)} datasets)")
        print("# " + "=" * 60)
        for cmd in commands:
            print(cmd)
        return True

    logger.info(f"Downloading {len(DATASETS_TH)} Thai datasets to {base_dir}")
    success = True
    for config in DATASETS_TH:
        if not download_dataset(config, base_dir, language):
            logger.error(f"Failed to download {config['name']}")
            success = False

    return success


def download_all_datasets(
    base_dir: Optional[str | Path] = None,
    languages: Optional[list[str]] = None,
    dry_run: bool = False,
) -> bool:
    """
    Download datasets for all (or specified) languages.

    Args:
        base_dir: Base directory for downloads (default: DATA_DIR)
        languages: List of language codes to download (default: all)
        dry_run: If True, only print commands without executing

    Returns:
        True if all downloads succeeded (or dry_run), False otherwise
    """
    if languages is None:
        languages = ["ar", "tr", "hi", "it", "th"]

    success = True

    if "ar" in languages:
        if not download_arabic_datasets(base_dir, dry_run):
            success = False

    if "tr" in languages:
        if not download_turkish_datasets(base_dir, dry_run):
            success = False

    if "hi" in languages:
        if not download_hindi_datasets(base_dir, dry_run):
            success = False

    if "it" in languages:
        if not download_italian_datasets(base_dir, dry_run):
            success = False

    if "th" in languages:
        if not download_thai_datasets(base_dir, dry_run):
            success = False

    return success


def print_download_commands(language: str = "all") -> None:
    """
    Print download commands for datasets.

    Useful for manual execution or scripting.

    Args:
        language: Language code (ar, tr, hi, it, th) or "all"
    """
    if language == "all":
        download_all_datasets(dry_run=True)
    elif language == "ar":
        download_arabic_datasets(dry_run=True)
    elif language == "tr":
        download_turkish_datasets(dry_run=True)
    elif language == "hi":
        download_hindi_datasets(dry_run=True)
    elif language == "it":
        download_italian_datasets(dry_run=True)
    elif language == "th":
        download_thai_datasets(dry_run=True)
    else:
        print(f"Unknown language: {language}. Use: ar, tr, hi, it, th, or all")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download HuggingFace datasets")
    parser.add_argument(
        "--language", "-l",
        choices=["ar", "tr", "hi", "it", "th", "all"],
        default="all",
        help="Language to download (default: all)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Print commands without executing"
    )
    parser.add_argument(
        "--base-dir", "-d",
        type=str,
        default=None,
        help="Base directory for downloads"
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.language == "all":
        download_all_datasets(args.base_dir, dry_run=args.dry_run)
    else:
        download_all_datasets(args.base_dir, [args.language], args.dry_run)
