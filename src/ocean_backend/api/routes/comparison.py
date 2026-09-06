from fastapi import APIRouter, HTTPException

from ocean_backend.data.argo.adapter import ArgoAdapter
from ocean_backend.data.observation_store import ObservationStore
from ocean_backend.models.schemas import ComparisonRequest, ComparisonEvidence
from ocean_backend.services.model_service import ModelService


router = APIRouter(
    prefix="/comparison",
    tags=["comparison"],
)


MODEL_PATH = "src/ocean_backend/data/model_argo_1902675.nc"
ARGO_PATH = "src/ocean_backend/data/argo/profiles/1902675_prof.nc"


# Load real Argo GDAC observations.
argo_adapter = ArgoAdapter(ARGO_PATH)
argo_observations = argo_adapter.load_observations()

observation_store = ObservationStore(argo_observations)

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