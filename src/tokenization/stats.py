"""Token statistics logging and persistence."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TokenStatsLogger:
    """
    Logger for token statistics across pipeline stages.

    Maintains a JSON log file with token counts per language/stage/source,
    with timestamps for tracking progress over time.
    """

    def __init__(self, log_path: Path):
        """
        Initialize stats logger.

        Args:
            log_path: Path to JSON log file (will be created if doesn't exist)
        """
        self.log_path = Path(log_path)
        self.stats = self._load()

    def _load(self) -> dict:
        """Load existing stats from file or create new structure."""
        if self.log_path.exists():
            try:
                with open(self.log_path) as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse {self.log_path}, starting fresh")
        return {"stages": {}, "last_updated": None}

    def _save(self):
        """Save stats to file."""
        self.stats["last_updated"] = datetime.now().isoformat()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w") as f:
            json.dump(self.stats, f, indent=2)

    def log_stage(
        self,
        language: str,
        stage: str,
        source: str,
        stats: dict,
        extra: Optional[dict] = None,
    ):
        """
        Log token counts for a pipeline stage.

        Args:
            language: Language code (e.g., "tr", "hi", "ar")
            stage: Pipeline stage (e.g., "download", "filtered", "deduped", "consensus")
            source: Data source name (e.g., "hplt2", "culturax", "all")
            stats: Dict with at minimum "total_tokens" and "total_docs" keys
            extra: Optional extra metadata to include
        """
        key = f"{language}/{stage}/{source}"
        entry = {
            "tokens": stats.get("total_tokens", 0),
            "documents": stats.get("total_docs", 0),
            "timestamp": datetime.now().isoformat(),
        }
        if extra:
            entry["extra"] = extra

        self.stats["stages"][key] = entry
        self._save()

        logger.info(
            f"Logged {key}: {entry['tokens']:,} tokens, {entry['documents']:,} docs"
        )

    def get_stage(self, language: str, stage: str, source: str) -> Optional[dict]:
        """
        Get stats for a specific stage.

        Args:
            language: Language code
            stage: Pipeline stage
            source: Data source name

        Returns:
            Dict with tokens, documents, timestamp or None if not found
        """
        key = f"{language}/{stage}/{source}"
        return self.stats["stages"].get(key)

    def get_language_summary(self, language: str) -> dict:
        """
        Get summary of all stages for a language.

        Args:
            language: Language code

        Returns:
            Dict mapping stage/source to token counts
        """
        prefix = f"{language}/"
        return {
            k.replace(prefix, ""): v
            for k, v in self.stats["stages"].items()
            if k.startswith(prefix)
        }

    def print_summary(self, language: Optional[str] = None):
        """
        Print a human-readable summary of token stats.

        Args:
            language: If specified, only show stats for this language
        """
        print("\n" + "=" * 60)
        print("TOKEN STATISTICS SUMMARY")
        print("=" * 60)

        stages = self.stats["stages"]
        if language:
            prefix = f"{language}/"
            stages = {k: v for k, v in stages.items() if k.startswith(prefix)}

        if not stages:
            print("No statistics recorded yet.")
            return

        # Group by language
        by_language = {}
        for key, val in stages.items():
            parts = key.split("/")
            lang = parts[0]
            rest = "/".join(parts[1:])
            if lang not in by_language:
                by_language[lang] = {}
            by_language[lang][rest] = val

        for lang in sorted(by_language.keys()):
            print(f"\n{lang.upper()}:")
            print("-" * 40)
            for stage_source in sorted(by_language[lang].keys()):
                val = by_language[lang][stage_source]
                tokens = val["tokens"]
                docs = val["documents"]
                print(f"  {stage_source:<30} {tokens:>15,} tokens ({docs:,} docs)")

        print("\n" + "=" * 60)


__all__ = ["TokenStatsLogger"]
