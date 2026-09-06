"""Model service for scientific model-observation comparisons."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr

from ocean_backend.data.observation_store import ObservationStore
from ocean_backend.models.schemas import (
    ComparisonEvidence,
    ComparisonRequest,
)
from ocean_backend.science.collocation import build_collocation_result
from ocean_backend.science.interpolation import interpolate_4d


MODEL_VARIABLES = {
    "temperature": "thetao",
    "salinity": "so",
    "u": "uo",
    "v": "vo",
    "eastward_velocity": "uo",
    "northward_velocity": "vo",
}

OBSERVATION_VARIABLES = {
    "temperature": "thetao",
    "salinity": "so",
    "u": "uo",
    "v": "vo",
    "eastward_velocity": "uo",
    "northward_velocity": "vo",
}


class ModelService:
    """Load an ocean model dataset and perform scientific comparisons."""

    def __init__(
        self,
        dataset_path: str | Path,
        observation_store: ObservationStore | None = None,
    ) -> None:
        self.dataset_path = Path(dataset_path)

        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Model dataset not found: {self.dataset_path}"
            )

        self.dataset = xr.open_dataset(self.dataset_path)

        self.observation_store = (
            observation_store
            if observation_store is not None
            else ObservationStore()
        )

    def _validate_variable(self, variable: str) -> str:
        """Return the model variable corresponding to an API variable."""

        try:
            model_variable = MODEL_VARIABLES[variable]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported variable: {variable}"
            ) from exc

        if model_variable not in self.dataset:
            raise ValueError(
                f"Model dataset does not contain variable "
                f"'{model_variable}'."
            )

        return model_variable

    def _interpolate_model(
        self,
        variable: str,
        latitude: float,
        longitude: float,
        depth: float,
        time,
    ) -> float:
        """Interpolate a model variable at a requested 4D coordinate."""

        model_variable = self._validate_variable(variable)

        value = interpolate_4d(
            self.dataset[model_variable],
            latitude,
            longitude,
            depth,
            np.datetime64(time),
        )

        return float(value)

    def compare(
        self,
        request: ComparisonRequest,
    ) -> ComparisonEvidence:
        """
        Compare a model value with an observation when supplied.

        Without an observation_id:
            Return only the interpolated model value.

        With an observation_id:
            1. Find the observation closest to the requested depth.
            2. Interpolate the model at the observation's actual
               latitude, longitude, depth, and timestamp.
            3. Calculate model-observation difference.
            4. Preserve the requested-vs-observation depth separation.
            5. Calculate explainable confidence.
            6. Return traceable comparison evidence.
        """

        model_variable = self._validate_variable(
            request.variable
        )

        # ---------------------------------------------------------
        # MODEL-ONLY COMPARISON
        # ---------------------------------------------------------
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
                model_value=float(model_value),
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

        # ---------------------------------------------------------
        # FIND OBSERVATION
        # ---------------------------------------------------------
        profile_observation = (
            self.observation_store.get_by_id(
                request.observation_id
            )
        )

        if profile_observation is None:
            raise ValueError(
                f"Observation not found: "
                f"{request.observation_id}"
            )

        # ---------------------------------------------------------
        # VALIDATE OBSERVATION VARIABLE
        # ---------------------------------------------------------
        observation_variable = OBSERVATION_VARIABLES.get(
            request.variable
        )

        if observation_variable is None:
            raise ValueError(
                f"Unsupported observation variable: "
                f"{request.variable}"
            )

        has_matching_variable = any(
            observation.platform_id == request.observation_id
            and observation.variable == observation_variable
            for observation
            in self.observation_store.observations
        )

        if not has_matching_variable:
            raise ValueError(
                f"Observation variable "
                f"'{profile_observation.variable}' "
                f"does not match requested variable "
                f"'{request.variable}'"
            )

        # ---------------------------------------------------------
        # GET OBSERVATION CLOSEST TO REQUESTED DEPTH
        # ---------------------------------------------------------
        result = (
            self.observation_store.get_by_profile(
                profile_id=request.observation_id,
                variable=observation_variable,
                depth=request.depth_m,
            )
        )

        if result is None:
            raise ValueError(
                f"No observation found for profile "
                f"'{request.observation_id}' and variable "
                f"'{request.variable}'."
            )

        observation, depth_difference = result

        # ---------------------------------------------------------
        # SCIENTIFIC COLLOCATION
        #
        # The model value is evaluated at the observation's actual
        # latitude, longitude, depth, and timestamp.
        #
        # The requested depth remains separate from the observation
        # depth so that we can report how far apart they are.
        # ---------------------------------------------------------
        model_value = interpolate_4d(
            self.dataset[model_variable],
            observation.latitude,
            observation.longitude,
            observation.depth,
            np.datetime64(observation.time),
        )

        # ---------------------------------------------------------
        # BUILD TRACEABLE COMPARISON RESULT
        #
        # model_depth=request.depth_m is intentional here.
        #
        # It allows the evidence object to report:
        #
        # requested depth  = 300 m
        # observation      = 150 m
        # separation       = 150 m
        #
        # while the model itself is still interpolated at the
        # observation's actual depth.
        # ---------------------------------------------------------
        collocation = build_collocation_result(
            observation=observation,
            model_value=float(model_value),
            model_latitude=observation.latitude,
            model_longitude=observation.longitude,
            model_depth=request.depth_m,
            model_time=observation.time,
            interpolation_method=(
                "trilinear + linear temporal"
            ),
        )

        # ---------------------------------------------------------
        # API RESPONSE
        # ---------------------------------------------------------
        return ComparisonEvidence(
            variable=request.variable,
            requested=request,
            model_value=collocation.model_value,
            observed_value=collocation.observed_value,
            difference=collocation.difference,
            spatial_distance_km=collocation.distance_km,
            temporal_difference_hours=(
                collocation.time_difference_hours
            ),
            depth_difference_m=collocation.depth_difference_m,
            observation_qc=collocation.quality_flag,
            interpolation=collocation.interpolation_method,
            confidence=collocation.confidence,
            confidence_reasons=(
                collocation.confidence_reasons
            ),
        )

    def close(self) -> None:
        """Close the underlying xarray dataset."""

        self.dataset.close()

    def __enter__(self) -> "ModelService":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()