"""Comparison API routes."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from ocean_backend.data.argo.adapter import ArgoAdapter
from ocean_backend.data.observation_store import ObservationStore
from ocean_backend.models.schemas import (
    ComparisonEvidence,
    ComparisonRequest,
)
from ocean_backend.services.model_service import ModelService


router = APIRouter(
    prefix="/comparison",
    tags=["comparison"],
)


# ------------------------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------------------------

# comparison.py is located at:
#
# project/
# └── src/
#     └── ocean_backend/
#         └── api/
#             └── routes/
#                 └── comparison.py
#
# parents[0] = routes
# parents[1] = api
# parents[2] = ocean_backend
# parents[3] = src
# parents[4] = project root

PROJECT_ROOT = Path(__file__).resolve().parents[4]

DATA_DIR = (
    PROJECT_ROOT
    / "src"
    / "ocean_backend"
    / "data"
)


MODEL_PATH = (
    DATA_DIR
    / "model_argo_1902675.nc"
)


ARGO_PATH = (
    DATA_DIR
    / "argo"
    / "profiles"
    / "1902675_prof.nc"
)


# ------------------------------------------------------------------
# VALIDATE DATA FILES
# ------------------------------------------------------------------

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model dataset not found: {MODEL_PATH}"
    )


if not ARGO_PATH.exists():
    raise FileNotFoundError(
        f"Argo dataset not found: {ARGO_PATH}"
    )


# ------------------------------------------------------------------
# LOAD ARGO OBSERVATIONS
# ------------------------------------------------------------------

argo_adapter = ArgoAdapter(
    ARGO_PATH
)

argo_observations = (
    argo_adapter.load_observations()
)


observation_store = ObservationStore(
    argo_observations
)


# ------------------------------------------------------------------
# TEMPORARY DATA DIAGNOSTICS
# ------------------------------------------------------------------

print()
print("========== ANVIKSHA ARGO DEBUG ==========")
print("ARGO FILE:")
print(ARGO_PATH)

print(
    "OBSERVATION COUNT:",
    observation_store.count(),
)

platform_ids = sorted(
    set(
        str(observation.platform_id).strip()
        for observation
        in observation_store.observations
    )
)

print(
    "PLATFORM IDS:",
    platform_ids[:20],
)

print(
    "HAS PLATFORM 1902675:",
    "1902675" in platform_ids,
)

if observation_store.observations:
    first_observation = (
        observation_store.observations[0]
    )

    print(
        "FIRST OBSERVATION:",
        first_observation,
    )
else:
    print(
        "WARNING: NO ARGO OBSERVATIONS WERE LOADED."
    )

print("=========================================")
print()


# ------------------------------------------------------------------
# MODEL SERVICE
# ------------------------------------------------------------------

service = ModelService(
    MODEL_PATH,
    observation_store=observation_store,
)


# ------------------------------------------------------------------
# COMPARISON ENDPOINT
# ------------------------------------------------------------------

@router.post(
    "",
    response_model=ComparisonEvidence,
)
def compare(
    request: ComparisonRequest,
) -> ComparisonEvidence:
    """Compare an ocean model value with an Argo observation."""

    try:
        return service.compare(request)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc