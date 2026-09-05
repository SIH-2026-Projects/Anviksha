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
