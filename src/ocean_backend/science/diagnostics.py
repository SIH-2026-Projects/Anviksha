"""Oceanographic diagnostics.

Diagnostics are added only with explicit definitions, units, assumptions and tests.
"""

import numpy as np


def vertical_temperature_gradient(temperature, depth):
    """Compute dT/dz along the depth axis using numpy.gradient."""
    temperature = np.asarray(temperature, dtype=float)
    depth = np.asarray(depth, dtype=float)
    if temperature.shape[-1] != depth.size:
        raise ValueError("depth must match the last axis of temperature")
    return np.gradient(temperature, depth, axis=-1)
