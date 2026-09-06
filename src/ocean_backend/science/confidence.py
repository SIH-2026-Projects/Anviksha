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
) -> tuple[str, list[str]]:
    """
    Calculate deterministic confidence and explain why.
    """

    quality_flag = quality_flag.strip().upper()
    reasons = []

    if quality_flag == "FAIL":
        reasons.append("Observation failed quality control.")
        return "LOW", reasons

    if distance_km > 50.0:
        reasons.append("Large spatial separation.")

    if depth_difference_m > 25.0:
        reasons.append("Large depth separation.")

    if time_difference_hours > 24.0:
        reasons.append("Large temporal separation.")

    if reasons:
        return "LOW", reasons

    if quality_flag == "SUSPECT":
        reasons.append("Observation has a suspect quality flag.")
        return "MEDIUM", reasons

    if (
        distance_km <= 10.0
        and depth_difference_m <= 10.0
        and time_difference_hours <= 6.0
    ):
        reasons.extend([
            "Observation passed quality control.",
            "Small spatial separation.",
            "Small depth separation.",
            "Small temporal separation.",
        ])

        return "HIGH", reasons

    reasons.append("Comparison is usable but does not meet high-confidence criteria.")

    return "MEDIUM", reasons