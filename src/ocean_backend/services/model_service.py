"""Application service boundary between API routes and scientific/data layers."""

import numpy as np
import xarray as xr

from ocean_backend.data.observation_store import ObservationStore
from ocean_backend.models.schemas import ComparisonRequest, ComparisonEvidence
from ocean_backend.science.collocation import build_collocation_result
from ocean_backend.science.interpolation import interpolate_4d


MODEL_VARIABLES = {
    "temperature": "thetao",
    "salinity": "so",
    "u": "uo",
    "v": "vo",
}
OBSERVATION_VARIABLES = {
    "temperature": {"thetao", "temperature"},
    "salinity": {"so", "salinity"},
    "u": {"uo", "u"},
    "v": {"vo", "v"},
}


class ModelService:

    def __init__(
        self,
        dataset_path: str,
        observation_store: ObservationStore | None = None,
    ):
        self.dataset = xr.open_dataset(dataset_path)
        self.observation_store = observation_store or ObservationStore()

    def compare(self, request: ComparisonRequest) -> ComparisonEvidence:
     model_variable = MODEL_VARIABLES[request.variable]

     if request.observation_id is None:
        model_value = interpolate_4d(
            self.dataset[model_variable],
            request.latitude,
            request.longitude,
            request.depth_m,
            np.datetime64(request.time),
        )

        return ComparisonEvidence(
            variable=request.variable,
            requested=request,
            model_value=model_value,
            observed_value=None,
            difference=None,
            spatial_distance_km=None,
            temporal_difference_hours=None,
            depth_difference_m=None,
            observation_qc="UNKNOWN",
            interpolation="trilinear + linear temporal",
            confidence="UNAVAILABLE",
            confidence_reasons=[],
        )

     observation = self.observation_store.get_by_id(request.observation_id)

     if observation is None:
        raise ValueError(
            f"Observation not found: {request.observation_id}"
        )
        
     if observation.variable not in OBSERVATION_VARIABLES[request.variable]:
        raise ValueError(
            f"Observation variable '{observation.variable}' "
            f"does not match requested variable '{request.variable}'"
    )

     model_value = interpolate_4d(
        self.dataset[model_variable],
        observation.latitude,
        observation.longitude,
        observation.depth,
        np.datetime64(observation.time),
    )

     collocation = build_collocation_result(
        observation=observation,
        model_value=model_value,
        model_latitude=observation.latitude,
        model_longitude=observation.longitude,
        model_depth=observation.depth,
        model_time=observation.time,
        interpolation_method="trilinear + linear temporal",
    )

     return ComparisonEvidence(
        variable=request.variable,
        requested=request,
        model_value=collocation.model_value,
        observed_value=collocation.observed_value,
        difference=collocation.difference,
        spatial_distance_km=collocation.distance_km,
        temporal_difference_hours=collocation.time_difference_hours,
        depth_difference_m=collocation.depth_difference_m,
        observation_qc=collocation.quality_flag,
        interpolation=collocation.interpolation_method,
        confidence=collocation.confidence,
        confidence_reasons=collocation.confidence_reasons,
    )