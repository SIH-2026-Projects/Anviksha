from ocean_backend.data.observations import Observation
from ocean_backend.models.collocation import CollocationResult
from ocean_backend.science.comparison import model_observation_difference
from ocean_backend.science.depth import depth_difference_m
from ocean_backend.science.geo import distance_km
from ocean_backend.science.time import time_difference_hours
from ocean_backend.science.confidence import calculate_confidence

#attaching collocation layer






def build_collocation_result(
    observation: Observation,
    model_value: float,
    model_latitude: float,
    model_longitude: float,
    model_depth: float,
    model_time,
    interpolation_method: str,
) -> CollocationResult:
    """
    Build a model-observation collocation result.

    The model_value is assumed to have already been obtained
    through the appropriate model interpolation.
    """

    difference = model_observation_difference(
        model_value=model_value,
        observation_value=observation.value,
    )

    distance = distance_km(
        observation.latitude,
        observation.longitude,
        model_latitude,
        model_longitude,
    )

    depth_difference = depth_difference_m(
        observation.depth,
        model_depth,
    )

    time_difference = time_difference_hours(
        observation.time,
        model_time,
    )
    
    confidence = calculate_confidence(
    quality_flag=observation.quality_flag,
    distance_km=distance,
    depth_difference_m=depth_difference,
    time_difference_hours=time_difference,
)

    return CollocationResult(
        platform_id=observation.platform_id,
        variable=observation.variable,
        observed_value=observation.value,
        model_value=model_value,
        difference=difference,
        distance_km=distance,
        depth_difference_m=depth_difference,
        time_difference_hours=time_difference,
        confidence=confidence,
        interpolation_method=interpolation_method,
        quality_flag=observation.quality_flag,
    )