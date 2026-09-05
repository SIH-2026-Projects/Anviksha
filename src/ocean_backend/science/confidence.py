"""Deterministic comparability/confidence rules.

Thresholds are configuration, not hidden magic numbers. They will be defined only after
we establish the dataset/model resolution and observation characteristics.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Comparability:
    spatial_distance_km: float
    temporal_difference_hours: float
    depth_difference_m: float
    qc_passed: bool


# No production thresholds yet. We first need real source metadata and QC semantics.
# This module exists to freeze the interface without inventing scientific thresholds.


def classify_comparability(c: Comparability) -> str:
    if not c.qc_passed:
        return "UNAVAILABLE"
    return "UNAVAILABLE"

def calculate_confidence(
    quality_flag: str,
    distance_km: float,
    depth_difference_m: float,
    time_difference_hours: float,
) -> str:
    """
    Calculate deterministic confidence for a
    model-observation comparison.
    """

    quality_flag = quality_flag.strip().upper()

    if quality_flag == "FAIL":
        return "LOW"

    if (
        distance_km > 50.0
        or depth_difference_m > 25.0
        or time_difference_hours > 24.0
    ):
        return "LOW"

    if (
        quality_flag == "PASS"
        and distance_km <= 10.0
        and depth_difference_m <= 10.0
        and time_difference_hours <= 6.0
    ):
        return "HIGH"

    return "MEDIUM"