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
from ocean_backend.science.collocation import (
    build_collocation_result,
)
from ocean_backend.science.interpolation import (
    interpolate_4d,
)


# ------------------------------------------------------------------
# VARIABLE MAPPING
# ------------------------------------------------------------------

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
    """
    Scientific model access and model-observation
    comparison service.
    """

    def __init__(
        self,
        dataset_path: str | Path,
        observation_store: ObservationStore | None = None,
    ) -> None:

        self.dataset_path = Path(
            dataset_path
        )

        if not self.dataset_path.exists():
            raise FileNotFoundError(
                "Model dataset not found: "
                f"{self.dataset_path}"
            )

        self.dataset = xr.open_dataset(
            self.dataset_path
        )

        self.observation_store = (
            observation_store
            if observation_store is not None
            else ObservationStore()
        )

    # --------------------------------------------------------------
    # VARIABLE VALIDATION
    # --------------------------------------------------------------

    def _validate_variable(
        self,
        variable: str,
    ) -> str:
        """
        Validate the public variable name and return
        the corresponding model variable.
        """

        try:
            model_variable = (
                MODEL_VARIABLES[
                    variable
                ]
            )

        except KeyError as exc:
            raise ValueError(
                f"Unsupported variable: {variable}"
            ) from exc

        if (
            model_variable
            not in self.dataset
        ):
            raise ValueError(
                "Model dataset does not contain "
                f"variable '{model_variable}'."
            )

        return model_variable

    # --------------------------------------------------------------
    # MODEL INTERPOLATION
    # --------------------------------------------------------------

    def _interpolate_model(
        self,
        variable: str,
        latitude: float,
        longitude: float,
        depth: float,
        time,
    ) -> float:
        """
        Interpolate a model variable at a physical
        latitude/longitude/depth/time coordinate.
        """

        model_variable = (
            self._validate_variable(
                variable
            )
        )

        value = interpolate_4d(
            self.dataset[
                model_variable
            ],
            latitude,
            longitude,
            depth,
            np.datetime64(time),
        )

        return float(value)

    # --------------------------------------------------------------
    # OBSERVATION RESOLUTION
    # --------------------------------------------------------------

    def _resolve_observation(
        self,
        selector: str,
    ):
        """
        Resolve an observation selector.

        The current MVP accepts an Argo platform/float ID such as:

            1902675

        The ObservationStore performs the actual lookup.
        """

        selector = str(
            selector
        ).strip()

        if not selector:
            return None

        observation = (
            self.observation_store.get_by_id(
                selector
            )
        )

        if observation is not None:
            return observation

        observation = (
            self.observation_store.get_by_platform(
                selector
            )
        )

        if observation is not None:
            return observation

        return None

    # --------------------------------------------------------------
    # MAIN COMPARISON
    # --------------------------------------------------------------

    def compare(
        self,
        request: ComparisonRequest,
    ) -> ComparisonEvidence:
        """
        Compare a model value against an observation.

        Model-only request:
            observation_id is omitted.

        Model-observation request:
            observation_id is supplied.

        For observation comparison:

            1. Resolve Argo platform.
            2. Resolve requested variable.
            3. Select nearest measurement to requested depth.
            4. Evaluate model at the actual observation
               latitude/longitude/depth/time.
            5. Calculate model-observation difference.
            6. Calculate spatial separation.
            7. Calculate depth separation.
            8. Calculate temporal separation.
            9. Calculate confidence.
            10. Return scientific evidence.
        """

        model_variable = (
            self._validate_variable(
                request.variable
            )
        )

        # ==========================================================
        # MODEL-ONLY REQUEST
        # ==========================================================

        if request.observation_id is None:

            model_value = interpolate_4d(
                self.dataset[
                    model_variable
                ],
                request.latitude,
                request.longitude,
                request.depth_m,
                np.datetime64(
                    request.time
                ),
            )

            return ComparisonEvidence(
                variable=request.variable,
                requested=request,
                model_value=float(
                    model_value
                ),
                observed_value=None,
                difference=None,
                spatial_distance_km=None,
                temporal_difference_hours=None,
                depth_difference_m=None,
                observation_qc="UNKNOWN",
                interpolation=(
                    "trilinear + linear temporal"
                ),
                confidence="UNAVAILABLE",
                confidence_reasons=[],
            )

        # ==========================================================
        # RESOLVE OBSERVATION
        # ==========================================================

        selector = str(
            request.observation_id
        ).strip()

        profile_observation = (
            self._resolve_observation(
                selector
            )
        )

        if profile_observation is None:
            raise ValueError(
                f"Observation not found: {selector}"
            )

        # ==========================================================
        # OBSERVATION VARIABLE
        # ==========================================================

        try:
            observation_variable = (
                OBSERVATION_VARIABLES[
                    request.variable
                ]
            )

        except KeyError as exc:
            raise ValueError(
                "Unsupported observation variable: "
                f"{request.variable}"
            ) from exc

        # ==========================================================
        # VERIFY REQUESTED VARIABLE EXISTS FOR PLATFORM
        # ==========================================================

        resolved_platform_id = str(
            profile_observation.platform_id
        ).strip()

        has_matching_variable = any(
            (
                str(
                    observation.platform_id
                ).strip()
                == resolved_platform_id
                and
                str(
                    observation.variable
                ).strip()
                == observation_variable
            )
            for observation
            in self.observation_store.observations
        )

        if not has_matching_variable:
            raise ValueError(
                "Observation variable "
                f"'{profile_observation.variable}' "
                "does not match requested variable "
                f"'{request.variable}'"
            )

        # ==========================================================
        # SELECT NEAREST DEPTH MEASUREMENT
        # ==========================================================

        result = (
            self.observation_store.get_by_profile(
                profile_id=resolved_platform_id,
                variable=observation_variable,
                depth=request.depth_m,
            )
        )

        if result is None:
            raise ValueError(
                "No observation found for profile "
                f"'{resolved_platform_id}' and variable "
                f"'{request.variable}'."
            )

        observation, _depth_difference = result

        # ==========================================================
        # MODEL COLLLOCATION
        # ==========================================================
        #
        # IMPORTANT:
        #
        # Evaluate the model at the ACTUAL observation:
        #
        # M(
        #     lat_obs,
        #     lon_obs,
        #     depth_obs,
        #     time_obs
        # )
        #
        # This is compared against:
        #
        # O(
        #     lat_obs,
        #     lon_obs,
        #     depth_obs,
        #     time_obs
        # )
        #
        # This is the scientifically correct collocation
        # operation for the current MVP.
        #

        model_value = interpolate_4d(
            self.dataset[
                model_variable
            ],
            observation.latitude,
            observation.longitude,
            observation.depth,
            np.datetime64(
                observation.time
            ),
        )

        # ==========================================================
        # BUILD COLLOCATION RESULT
        # ==========================================================
        #
        # model_depth=request.depth_m is intentional.
        #
        # It preserves the difference between:
        #
        # requested comparison depth
        #
        # and
        #
        # actual selected observation depth.
        #
        # Example:
        #
        # requested = 150 m
        # observation = 145.54 m
        #
        # difference = 4.46 m
        #

        collocation = (
            build_collocation_result(
                observation=observation,
                model_value=float(
                    model_value
                ),
                model_latitude=(
                    observation.latitude
                ),
                model_longitude=(
                    observation.longitude
                ),
                model_depth=request.depth_m,
                model_time=(
                    observation.time
                ),
                interpolation_method=(
                    "trilinear + linear temporal"
                ),
            )
        )

        # ==========================================================
        # API RESPONSE
        # ==========================================================

        return ComparisonEvidence(
            variable=request.variable,
            requested=request,
            model_value=(
                collocation.model_value
            ),
            observed_value=(
                collocation.observed_value
            ),
            difference=(
                collocation.difference
            ),
            spatial_distance_km=(
                collocation.distance_km
            ),
            temporal_difference_hours=(
                collocation.time_difference_hours
            ),
            depth_difference_m=(
                collocation.depth_difference_m
            ),
            observation_qc=(
                collocation.quality_flag
            ),
            interpolation=(
                collocation.interpolation_method
            ),
            confidence=(
                collocation.confidence
            ),
            confidence_reasons=(
                collocation.confidence_reasons
            ),
        )

    # --------------------------------------------------------------
    # RESOURCE MANAGEMENT
    # --------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying xarray dataset."""
        self.dataset.close()

    def __enter__(
        self,
    ) -> "ModelService":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()