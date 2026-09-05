"""Application service boundary between API routes and scientific/data layers."""

from ocean_backend.models.schemas import ComparisonRequest, ComparisonEvidence


class ModelService:
    def compare(self, request: ComparisonRequest) -> ComparisonEvidence:
        raise NotImplementedError("Dataset-backed comparison is implemented after source inspection")
