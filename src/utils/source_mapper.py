"""Mapper to add source metadata to documents."""
from datatrove.pipeline.base import PipelineStep
from datatrove.data import Document


class AddSourceMapper(PipelineStep):
    """Adds source dataset name to document metadata."""

    name = "📝 Add Source"
    type = "🔄 - MAPPER"

    def __init__(self, source: str):
        super().__init__()
        self.source = source

    def run(self, data, rank: int = 0, world_size: int = 1):
        for doc in data:
            doc.metadata["source"] = self.source
            yield doc
