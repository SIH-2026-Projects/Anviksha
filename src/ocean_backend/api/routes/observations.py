"""Observation inspection endpoints."""

from fastapi import APIRouter

from ocean_backend.api.routes.comparison import (
    observation_store,
)

router = APIRouter(
    prefix="/observations",
    tags=["observations"],
)


@router.get("")
def list_observations() -> list[dict]:
    """
    Return a lightweight list of loaded observations.

    Intended for frontend discovery/debugging.
    """
    return [
        {
            "platform_id": observation.platform_id,
            "latitude": observation.latitude,
            "longitude": observation.longitude,
            "depth": observation.depth,
            "time": observation.time,
            "variable": observation.variable,
            "value": observation.value,
            "quality_flag": observation.quality_flag,
            "cycle_number": observation.cycle_number,
            "value_source": observation.value_source,
            "data_mode": observation.data_mode,
        }
        for observation in observation_store.observations
    ]