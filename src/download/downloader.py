"""
Generic HuggingFace dataset download utilities.

This module provides functions to download datasets using the HuggingFace CLI
with support for selective downloads using --include patterns.
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def download_with_cli(
    repo_id: str,
    local_dir: str | Path,
    include_pattern: Optional[str] = None,
    repo_type: str = "dataset",
    revision: Optional[str] = None,
    token: Optional[str] = None,
    resume: bool = True,
) -> bool:
    """
    Download a HuggingFace dataset using the CLI.

    This is preferred over the Python API for large datasets as it:
    - Supports selective downloads with --include patterns
    - Has better resume capabilities
    - Is more memory efficient

    Args:
        repo_id: HuggingFace repository ID (e.g., "HPLT/HPLT2.0_cleaned")
        local_dir: Local directory to download to
        include_pattern: Glob pattern for selective download (e.g., "tur_Latn/*")
        repo_type: Type of repository ("dataset", "model", "space")
        revision: Specific revision/branch to download
        token: HuggingFace token for private repos
        resume: Whether to resume interrupted downloads

    Returns:
        True if download succeeded, False otherwise
    """
    local_dir = Path(local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "huggingface-cli",
        "download",
        repo_id,
        "--repo-type", repo_type,
        "--local-dir", str(local_dir),
    ]

    if include_pattern:
        cmd.extend(["--include", include_pattern])

    if revision:
        cmd.extend(["--revision", revision])

    if token:
        cmd.extend(["--token", token])

    if resume:
        cmd.append("--resume-download")

    logger.info(f"Downloading {repo_id} to {local_dir}")
    if include_pattern:
        logger.info(f"  Include pattern: {include_pattern}")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Successfully downloaded {repo_id}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to download {repo_id}: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("huggingface-cli not found. Install with: pip install huggingface_hub")
        return False


def download_dataset(
    dataset_config: dict,
    base_dir: str | Path,
    language: str,
) -> bool:
    """
    Download a single dataset based on its configuration.

    Args:
        dataset_config: Dataset configuration dict with keys:
            - name: HuggingFace repo ID
            - subset: Subset/config name (used to build include pattern)
            - output_name: Local directory name
            - special_handling: Optional flag for special cases (e.g., "sangraha")
        base_dir: Base directory for downloads
        language: Language code (ar, tr, hi)

    Returns:
        True if download succeeded, False otherwise
    """
    base_dir = Path(base_dir)
    repo_id = dataset_config["name"]
    subset = dataset_config.get("subset")
    output_name = dataset_config["output_name"]
    special_handling = dataset_config.get("special_handling")

    local_dir = base_dir / language / "downloads" / output_name

    # Build include pattern based on subset
    include_pattern = None
    if subset:
        # Handle different dataset structures
        if "HPLT" in repo_id:
            include_pattern = f"{subset}/*"
        elif "fineweb-2" in repo_id:
            include_pattern = f"data/{subset}/*"
        elif "finepdfs" in repo_id:
            include_pattern = f"data/{subset}/*"
        elif "CulturaX" in repo_id:
            include_pattern = f"{subset}/*"
        elif "c4" in repo_id:
            include_pattern = f"multilingual/c4-{subset}*"
        elif special_handling == "sangraha":
            # Sangraha uses a special path structure
            include_pattern = f"{subset}/*"
        elif special_handling == "sea_cc" or "sea-commoncrawl" in repo_id:
            # SEA CommonCrawl uses language folder structure
            include_pattern = f"{subset}/*"

    return download_with_cli(
        repo_id=repo_id,
        local_dir=local_dir,
        include_pattern=include_pattern,
    )


def get_download_commands(
    datasets: list[dict],
    base_dir: str | Path,
    language: str,
) -> list[str]:
    """
    Generate shell commands for downloading datasets.

    Useful for manual execution or scripting.

    Args:
        datasets: List of dataset configuration dicts
        base_dir: Base directory for downloads
        language: Language code (ar, tr, hi)

    Returns:
        List of shell commands to execute
    """
    base_dir = Path(base_dir)
    commands = []

    for config in datasets:
        repo_id = config["name"]
        subset = config.get("subset")
        output_name = config["output_name"]
        special_handling = config.get("special_handling")

        local_dir = base_dir / language / "downloads" / output_name

        cmd = f"huggingface-cli download {repo_id} --repo-type dataset"

        # Build include pattern
        if subset:
            if "HPLT" in repo_id:
                cmd += f" --include '{subset}/*'"
            elif "fineweb-2" in repo_id:
                cmd += f" --include 'data/{subset}/*'"
            elif "finepdfs" in repo_id:
                cmd += f" --include 'data/{subset}/*'"
            elif "CulturaX" in repo_id:
                cmd += f" --include '{subset}/*'"
            elif "c4" in repo_id:
                cmd += f" --include 'multilingual/c4-{subset}*'"
            elif special_handling == "sangraha":
                cmd += f" --include '{subset}/*'"
            elif special_handling == "sea_cc" or "sea-commoncrawl" in repo_id:
                cmd += f" --include '{subset}/*'"

        cmd += f" --local-dir {local_dir}"
        commands.append(cmd)

    return commands
