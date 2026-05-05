"""Schema-enforcing Parquet writer for standardized output."""
import logging
from pathlib import Path
from typing import Iterator, Optional

import pyarrow as pa
import pyarrow.parquet as pq
from datatrove.data import Document
from datatrove.pipeline.writers import DiskWriter

from src.utils.id_generator import generate_id
from src.config.schema import STANDARD_SCHEMA
from src.config.common import PARQUET_CONFIG

logger = logging.getLogger(__name__)


class SchemaEnforcingWriter(DiskWriter):
    """
    ParquetWriter that enforces the standard output schema.

    Ensures all output has consistent columns: text, id (hash), source.
    Applies proper Parquet settings for HuggingFace compatibility.
    """

    name = "SchemaEnforcingWriter"

    def __init__(
        self,
        output_folder: str,
        source_name: str,
        output_filename: str = "${rank}.parquet",
        max_file_size: int = 5 * 1024 * 1024 * 1024,  # 5GB max
    ):
        """
        Initialize writer.

        Args:
            output_folder: Directory for output files
            source_name: Source dataset name (e.g., "hplt2", "culturax")
            output_filename: Output filename pattern (supports ${rank})
            max_file_size: Max file size before rotation (default 5GB)
        """
        super().__init__(
            output_folder=output_folder,
            output_filename=output_filename,
            max_file_size=max_file_size,
        )
        self.source_name = source_name
        self._buffer = []
        self._buffer_size = 10000  # Batch size for writes
        self._file_counter = 0
        self._output_folder = Path(output_folder)
        self._output_folder.mkdir(parents=True, exist_ok=True)

    def document_to_row(self, doc: Document) -> dict:
        """
        Convert DataTrove Document to standardized row.

        Args:
            doc: DataTrove Document object

        Returns:
            Dict with text, id, source columns
        """
        return {
            "text": doc.text,
            "id": generate_id(doc.text),
            "source": self.source_name,
        }

    def write(self, document: Document, rank: int = 0):
        """
        Buffer document for batch writing.

        Args:
            document: DataTrove Document
            rank: Worker rank for filename
        """
        self._buffer.append(self.document_to_row(document))

        if len(self._buffer) >= self._buffer_size:
            self._flush_buffer(rank)

    def _flush_buffer(self, rank: int = 0):
        """Flush buffer to parquet file."""
        if not self._buffer:
            return

        table = pa.Table.from_pylist(self._buffer, schema=STANDARD_SCHEMA)

        output_path = self._output_folder / f"{rank}_{self._file_counter:05d}.parquet"
        pq.write_table(
            table,
            output_path,
            row_group_size=PARQUET_CONFIG["row_group_size"],
            write_page_index=PARQUET_CONFIG["write_page_index"],
            compression=PARQUET_CONFIG["compression"],
        )

        logger.debug(f"Wrote {len(self._buffer)} rows to {output_path}")
        self._buffer = []
        self._file_counter += 1

    def close(self, rank: int = 0):
        """Flush remaining buffer on close."""
        self._flush_buffer(rank)


def write_documents_to_parquet(
    documents: Iterator[Document],
    output_path: Path,
    source_name: str,
    batch_size: int = 50000,
) -> int:
    """
    Write documents to parquet with standard schema.

    Utility function for writing documents outside of DataTrove pipeline.

    Args:
        documents: Iterator of Document objects
        output_path: Output parquet file path
        source_name: Source dataset name
        batch_size: Number of documents per write batch

    Returns:
        Number of documents written
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    total_written = 0

    for doc in documents:
        rows.append({
            "text": doc.text,
            "id": generate_id(doc.text),
            "source": source_name,
        })

        if len(rows) >= batch_size:
            table = pa.Table.from_pylist(rows, schema=STANDARD_SCHEMA)
            # Append mode
            if output_path.exists():
                existing = pq.read_table(output_path)
                table = pa.concat_tables([existing, table])

            pq.write_table(
                table,
                output_path,
                row_group_size=PARQUET_CONFIG["row_group_size"],
                write_page_index=PARQUET_CONFIG["write_page_index"],
                compression=PARQUET_CONFIG["compression"],
            )
            total_written += len(rows)
            rows = []

    # Write remaining
    if rows:
        table = pa.Table.from_pylist(rows, schema=STANDARD_SCHEMA)
        if output_path.exists():
            existing = pq.read_table(output_path)
            table = pa.concat_tables([existing, table])

        pq.write_table(
            table,
            output_path,
            row_group_size=PARQUET_CONFIG["row_group_size"],
            write_page_index=PARQUET_CONFIG["write_page_index"],
            compression=PARQUET_CONFIG["compression"],
        )
        total_written += len(rows)

    return total_written


__all__ = ["SchemaEnforcingWriter", "write_documents_to_parquet"]
