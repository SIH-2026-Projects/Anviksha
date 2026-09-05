"""Observation access boundary.

Argo/Glider adapters should normalize into this boundary rather than leaking source-specific
field names into the scientific engine.
"""

from ocean_backend.models.schemas import ObservationPoint


class ObservationRepository:
    def get(self, observation_id: str) -> ObservationPoint | None:
        raise NotImplementedError
