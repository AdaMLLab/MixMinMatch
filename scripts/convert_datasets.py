#!/usr/bin/env python3
"""
Convert non-standard datasets to parquet format for the pipeline.

Handles:
- HPLT2: Already parquet but with complex schema - extract text only
- C4: JSON.GZ format
- SEA CommonCrawl: JSONL format
"""
import argparse
import gzip
import json
import logging
import os
from pathlib import Path
from hashlib import md5

import pyarrow as pa
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Standard schema for pipeline
STANDARD_SCHEMA = pa.schema([
    ("text", pa.string()),
    ("id", pa.string()),
    ("source", pa.string()),
])


def generate_id(text: str) -> str:
    """Generate 12-char MD5 hash from normalized text."""
    normalized = " ".join(text.lower().split())
    return md5(normalized.encode()).hexdigest()[:12]


def convert_hplt2(input_dir: Path, output_dir: Path, source_name: str = "hplt2"):
    """
    Convert HPLT2 parquet files to standard schema.
    HPLT2 has complex schema - we only need the 'text' column.
    """
    logger.info(f"Converting HPLT2 from {input_dir} to {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    parquet_files = list(input_dir.rglob("*.parquet"))
    logger.info(f"Found {len(parquet_files)} parquet files")

    total_docs = 0
    for i, pq_file in enumerate(parquet_files):
        logger.info(f"Processing {i+1}/{len(parquet_files)}: {pq_file.name}")

        try:
            table = pq.read_table(pq_file, columns=["text"])
            texts = table.column("text").to_pylist()

            ids = [generate_id(t) for t in texts]
            sources = [source_name] * len(texts)

            new_table = pa.table({
                "text": texts,
                "id": ids,
                "source": sources,
            }, schema=STANDARD_SCHEMA)

            output_file = output_dir / f"{pq_file.stem}.parquet"
            pq.write_table(new_table, output_file)

            total_docs += len(texts)
            logger.info(f"  Converted {len(texts)} docs")

        except Exception as e:
            logger.error(f"  Error: {e}")
            continue

    logger.info(f"Total: {total_docs} documents converted")


def convert_c4_jsongz(input_dir: Path, output_dir: Path, source_name: str = "c4_th"):
    """
    Convert C4 json.gz files to parquet.
    Each line is a JSON object with 'text' field.
    """
    logger.info(f"Converting C4 from {input_dir} to {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    gz_files = list(input_dir.rglob("*.json.gz"))
    logger.info(f"Found {len(gz_files)} json.gz files")

    total_docs = 0
    batch_size = 100000  # Write every 100K docs

    texts = []
    ids = []
    sources = []
    file_counter = 0

    for i, gz_file in enumerate(gz_files):
        if i % 50 == 0:
            logger.info(f"Processing {i+1}/{len(gz_files)}: {gz_file.name}")

        try:
            with gzip.open(gz_file, 'rt', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        text = data.get("text", "")
                        if text:
                            texts.append(text)
                            ids.append(generate_id(text))
                            sources.append(source_name)
                            total_docs += 1

                            if len(texts) >= batch_size:
                                # Write batch
                                table = pa.table({
                                    "text": texts,
                                    "id": ids,
                                    "source": sources,
                                }, schema=STANDARD_SCHEMA)

                                output_file = output_dir / f"part_{file_counter:05d}.parquet"
                                pq.write_table(table, output_file)
                                logger.info(f"  Wrote {len(texts)} docs to {output_file.name}")

                                texts = []
                                ids = []
                                sources = []
                                file_counter += 1

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"  Error processing {gz_file}: {e}")
            continue

    # Write remaining
    if texts:
        table = pa.table({
            "text": texts,
            "id": ids,
            "source": sources,
        }, schema=STANDARD_SCHEMA)

        output_file = output_dir / f"part_{file_counter:05d}.parquet"
        pq.write_table(table, output_file)
        logger.info(f"  Wrote {len(texts)} docs to {output_file.name}")

    logger.info(f"Total: {total_docs} documents converted")


def convert_sea_jsonl(input_dir: Path, output_dir: Path, source_name: str = "sea_cc"):
    """
    Convert SEA CommonCrawl jsonl files to parquet.
    """
    logger.info(f"Converting SEA CommonCrawl from {input_dir} to {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_files = list(input_dir.rglob("*.jsonl"))
    if not jsonl_files:
        # Check for files without extension
        jsonl_files = [f for f in input_dir.rglob("*") if f.is_file() and "chunk" in f.name]

    logger.info(f"Found {len(jsonl_files)} jsonl files")

    total_docs = 0
    batch_size = 100000

    texts = []
    ids = []
    sources = []
    file_counter = 0

    for i, jsonl_file in enumerate(jsonl_files):
        if i % 10 == 0:
            logger.info(f"Processing {i+1}/{len(jsonl_files)}: {jsonl_file.name}")

        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        text = data.get("text", "")
                        if text:
                            texts.append(text)
                            ids.append(generate_id(text))
                            sources.append(source_name)
                            total_docs += 1

                            if len(texts) >= batch_size:
                                table = pa.table({
                                    "text": texts,
                                    "id": ids,
                                    "source": sources,
                                }, schema=STANDARD_SCHEMA)

                                output_file = output_dir / f"part_{file_counter:05d}.parquet"
                                pq.write_table(table, output_file)
                                logger.info(f"  Wrote {len(texts)} docs to {output_file.name}")

                                texts = []
                                ids = []
                                sources = []
                                file_counter += 1

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"  Error processing {jsonl_file}: {e}")
            continue

    # Write remaining
    if texts:
        table = pa.table({
            "text": texts,
            "id": ids,
            "source": sources,
        }, schema=STANDARD_SCHEMA)

        output_file = output_dir / f"part_{file_counter:05d}.parquet"
        pq.write_table(table, output_file)
        logger.info(f"  Wrote {len(texts)} docs to {output_file.name}")

    logger.info(f"Total: {total_docs} documents converted")


def main():
    parser = argparse.ArgumentParser(description="Convert datasets to parquet format")
    parser.add_argument("--dataset", choices=["hplt2", "c4", "sea_cc", "all"], required=True)
    parser.add_argument("--language", "-l", default="th", help="Language code")
    parser.add_argument("--base-dir", default="data", help="Base data directory")

    args = parser.parse_args()
    base_dir = Path(args.base_dir) / args.language

    if args.dataset in ["hplt2", "all"]:
        input_dir = base_dir / "downloads" / "hplt2"
        output_dir = base_dir / "downloads_converted" / "hplt2"
        if input_dir.exists():
            convert_hplt2(input_dir, output_dir)

    if args.dataset in ["c4", "all"]:
        input_dir = base_dir / "downloads" / "c4_th" / "multilingual"
        output_dir = base_dir / "downloads_converted" / "c4_th"
        if input_dir.exists():
            convert_c4_jsongz(input_dir, output_dir)

    if args.dataset in ["sea_cc", "all"]:
        input_dir = base_dir / "downloads" / "sea_cc" / "thai"
        output_dir = base_dir / "downloads_converted" / "sea_cc"
        if input_dir.exists():
            convert_sea_jsonl(input_dir, output_dir)


if __name__ == "__main__":
    main()
