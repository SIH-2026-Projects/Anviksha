from dataclasses import dataclass
from datetime import datetime


@dataclass
class Observation:
    """
    A single in-situ ocean observation.
    creating aaa data structure representing
Observation
├── latitude
├── longitude
├── depth
├── time
├── variable
├── value
├── platform_id
└── quality flag

    Represents one measurement made by an instrument
    at a specific location, depth, and time.
    """

    platform_id: str
    latitude: float
    longitude: float
    depth: float
    time: datetime
    variable: str
    value: float
    quality_flag: str
    