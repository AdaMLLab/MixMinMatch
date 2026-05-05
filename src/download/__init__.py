"""Download utilities for HuggingFace datasets."""
from .downloader import download_dataset, download_with_cli
from .hf_download import (
    download_arabic_datasets,
    download_turkish_datasets,
    download_hindi_datasets,
    download_italian_datasets,
    download_thai_datasets,
    download_all_datasets,
)

__all__ = [
    "download_dataset",
    "download_with_cli",
    "download_arabic_datasets",
    "download_turkish_datasets",
    "download_hindi_datasets",
    "download_italian_datasets",
    "download_thai_datasets",
    "download_all_datasets",
]
