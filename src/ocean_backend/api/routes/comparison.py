from datetime import datetime

from fastapi import APIRouter, HTTPException

from ocean_backend.data.observations import Observation
from ocean_backend.data.observation_store import ObservationStore
from ocean_backend.models.schemas import ComparisonRequest, ComparisonEvidence
from ocean_backend.services.model_service import ModelService


router = APIRouter(
    prefix="/comparison",
    tags=["comparison"],
)


MODEL_PATH = "src/ocean_backend/data/model_4d.nc"

demo_observation = Observation(
    platform_id="ARGO_TEST_001",
    latitude=12.5,
    longitude=70.5,
    depth=150.0,
    time=datetime(2026, 6, 22, 12),
    variable="thetao",
    value=18.91,
    quality_flag="PASS",
)

observation_store = ObservationStore([demo_observation])

service = ModelService(
    MODEL_PATH,
    observation_store=observation_store,
)


@router.post("", response_model=ComparisonEvidence)
def compare(request: ComparisonRequest) -> ComparisonEvidence:
    try:
        return service.compare(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc