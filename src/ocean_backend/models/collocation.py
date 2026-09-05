from dataclasses import dataclass


@dataclass
class CollocationResult:
    """
    Result of comparing an observation with a model value
    at the corresponding location, depth, and time.
    """

    platform_id: str
    variable: str

    observed_value: float
    model_value: float
    difference: float

    distance_km: float
    depth_difference_m: float
    time_difference_hours: float

    confidence: str
    interpolation_method: str
    quality_flag: str