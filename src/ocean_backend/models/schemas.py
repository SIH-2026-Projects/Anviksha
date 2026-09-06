"""API request and response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


VariableName = Literal[
    "temperature",
    "salinity",
    "u",
    "v",
    "chlorophyll",
]

ConfidenceLevel = Literal[
    "HIGH",
    "MEDIUM",
    "LOW",
    "UNAVAILABLE",
]

QCStatus = Literal[
    "PASS",
    "SUSPECT",
    "FAIL",
    "UNKNOWN",
]


class Coordinate4D(BaseModel):
    """A location in latitude, longitude, depth, and time."""

    latitude: float = Field(
        ge=-90,
        le=90,
        description="Latitude in degrees.",
    )

    longitude: float = Field(
        ge=-180,
        le=180,
        description="Longitude in degrees.",
    )

    depth_m: float = Field(
        ge=0,
        description="Depth below sea surface in metres.",
    )

    time: datetime = Field(
        description="Observation/model time.",
    )


class ObservationPoint(Coordinate4D):
    """An individual observation point."""

    observation_id: str

    variable: VariableName

    value: float

    qc: QCStatus = "UNKNOWN"


class ComparisonRequest(Coordinate4D):
    """Request for a model or model-observation comparison."""

    variable: VariableName

    observation_id: str | None = None


class ComparisonEvidence(BaseModel):
    """
    Evidence returned by the scientific comparison engine.

    The difference is a model-observation difference.
    It should not automatically be interpreted as pure model error.
    """

    variable: VariableName

    requested: Coordinate4D

    model_value: float | None = Field(
        description="Interpolated model value at the comparison point.",
    )

    observed_value: float | None = Field(
        description="Selected quality-controlled observation value.",
    )

    difference: float | None = Field(
        description="Model value minus observed value.",
    )

    spatial_distance_km: float | None = Field(
        description=(
            "Distance from the observation to the nearest "
            "model horizontal grid point."
        ),
    )

    temporal_difference_hours: float | None = Field(
        description=(
            "Absolute time difference between the observation "
            "and the nearest model output time."
        ),
    )

    depth_difference_m: float | None = Field(
        description=(
            "Absolute depth difference between the selected "
            "observation measurement and the requested depth."
        ),
    )

    observation_qc: QCStatus

    interpolation: str | None = Field(
        description="Interpolation method used to obtain the model value.",
    )

    confidence: ConfidenceLevel = Field(
        description=(
            "Confidence in the comparability of the evidence, "
            "not a statement that the model is correct."
        ),
    )

    confidence_reasons: list[str] = Field(
        description="Human-readable reasons supporting the confidence level.",
    )