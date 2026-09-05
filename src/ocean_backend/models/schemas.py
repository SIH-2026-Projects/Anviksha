from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


VariableName = Literal["temperature", "salinity", "u", "v", "chlorophyll"]
ConfidenceLevel = Literal["HIGH", "MEDIUM", "LOW", "UNAVAILABLE"]
QCStatus = Literal["PASS", "SUSPECT", "FAIL", "UNKNOWN"]


class Coordinate4D(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    depth_m: float = Field(ge=0)
    time: datetime


class ObservationPoint(Coordinate4D):
    observation_id: str
    variable: VariableName
    value: float
    qc: QCStatus = "UNKNOWN"


class ComparisonRequest(Coordinate4D):
    variable: VariableName
    observation_id: str | None = None


class ComparisonEvidence(BaseModel):
    variable: VariableName
    requested: Coordinate4D
    model_value: float | None
    observed_value: float | None
    difference: float | None
    spatial_distance_km: float | None
    temporal_difference_hours: float | None
    depth_difference_m: float | None
    observation_qc: QCStatus
    interpolation: str | None
    confidence: ConfidenceLevel
