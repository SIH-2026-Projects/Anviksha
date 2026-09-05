"""Pure numerical interpolation helpers.

These functions intentionally do not know anything about HTTP, databases, or file formats.
"""

import numpy as np
import xarray as xr


def linear_time(v0: float, v1: float, alpha: float) -> float:
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be between 0 and 1")
    return float((1.0 - alpha) * v0 + alpha * v1)


def trilinear(corners: np.ndarray, wx: float, wy: float, wz: float) -> float:
    """Interpolate an eight-corner regular-grid cell.

    corners is indexed [x, y, z] and must have shape (2, 2, 2).
    """
    arr = np.asarray(corners, dtype=float)
    if arr.shape != (2, 2, 2):
        raise ValueError("corners must have shape (2, 2, 2)")
    for weight in (wx, wy, wz):
        if not 0.0 <= weight <= 1.0:
            raise ValueError("interpolation weights must be between 0 and 1")

    total = 0.0
    for i in range(2):
        for j in range(2):
            for k in range(2):
                weight = (
                    (wx if i else 1.0 - wx)
                    * (wy if j else 1.0 - wy)
                    * (wz if k else 1.0 - wz)
                )
                total += weight * arr[i, j, k]
    return float(total)


def bilinear_spatial(
    field: xr.DataArray,
    latitude: float,
    longitude: float,
) -> float:
    """
    Bilinearly interpolate a field on a regular latitude/longitude grid.

    The field must contain latitude and longitude dimensions.

    Returns:
        Interpolated model value.

    Raises:
        ValueError: If the requested point is outside the model domain
                    or if surrounding values are invalid.
    """

    if "latitude" not in field.dims:
        raise ValueError("Field must contain a latitude dimension.")

    if "longitude" not in field.dims:
        raise ValueError("Field must contain a longitude dimension.")

    latitudes = field["latitude"].values
    longitudes = field["longitude"].values

    if latitude < latitudes.min() or latitude > latitudes.max():
        raise ValueError("Latitude is outside the model domain.")

    if longitude < longitudes.min() or longitude > longitudes.max():
        raise ValueError("Longitude is outside the model domain.")

    lat_index = np.searchsorted(latitudes, latitude)

    lon_index = np.searchsorted(longitudes, longitude)

    lat_index = min(max(lat_index, 1), len(latitudes) - 1)
    lon_index = min(max(lon_index, 1), len(longitudes) - 1)

    lat0 = latitudes[lat_index - 1]
    lat1 = latitudes[lat_index]

    lon0 = longitudes[lon_index - 1]
    lon1 = longitudes[lon_index]

    values = field.sel(
        latitude=slice(lat0, lat1),
        longitude=slice(lon0, lon1),
    )

    # Remove dimensions that contain exactly one value.
    values = values.squeeze(drop=True)

    if "time" in values.dims:
        values = values.isel(time=0)

    if "depth" in values.dims:
        values = values.isel(depth=0)

    q11 = float(values.sel(latitude=lat0, longitude=lon0).values)
    q21 = float(values.sel(latitude=lat1, longitude=lon0).values)
    q12 = float(values.sel(latitude=lat0, longitude=lon1).values)
    q22 = float(values.sel(latitude=lat1, longitude=lon1).values)

    corners = np.array([q11, q21, q12, q22])

    if np.any(np.isnan(corners)):
        raise ValueError(
            "Cannot interpolate because one or more surrounding model values are invalid."
        )

    a = (latitude - lat0) / (lat1 - lat0)
    b = (longitude - lon0) / (lon1 - lon0)

    result = (
        (1 - a) * (1 - b) * q11
        + a * (1 - b) * q21
        + (1 - a) * b * q12
        + a * b * q22
    )

    return float(result)

def linear_depth(
    field: xr.DataArray,
    depth: float,
) -> float:
    """
    Linearly interpolate a field along its physical depth coordinate.

    The depth coordinate is expected to be positive downward.
    """

    if "depth" not in field.dims:
        raise ValueError("Field must contain a depth dimension.")

    depths = field["depth"].values

    if depth < depths.min() or depth > depths.max():
        raise ValueError("Depth is outside the model domain.")

    depth_index = np.searchsorted(depths, depth)

    if depth_index == 0:
        depth_index = 1

    if depth_index == len(depths):
        depth_index = len(depths) - 1

    depth0 = depths[depth_index - 1]
    depth1 = depths[depth_index]

    value0 = field.sel(depth=depth0)
    value1 = field.sel(depth=depth1)

    value0 = value0.squeeze(drop=True)
    value1 = value1.squeeze(drop=True)

    if "time" in value0.dims:
        value0 = value0.isel(time=0)

    if "time" in value1.dims:
        value1 = value1.isel(time=0)

    value0 = float(value0.values)
    value1 = float(value1.values)

    if np.isnan(value0) or np.isnan(value1):
        raise ValueError(
            "Cannot interpolate because one or more surrounding "
            "model values are invalid."
        )

    weight = (depth - depth0) / (depth1 - depth0)

    result = (1 - weight) * value0 + weight * value1

    return float(result)

def interpolate_3d(
    field: xr.DataArray,
    latitude: float,
    longitude: float,
    depth: float,
) -> float:
    """
    Trilinearly interpolate a CF-aware ocean model field.

    The field must contain:
        latitude
        longitude
        depth

    Depth is assumed to be positive downward according to CF metadata.
    """

    required_dims = {"latitude", "longitude", "depth"}

    missing = required_dims - set(field.dims)

    if missing:
        raise ValueError(
            f"Field is missing required dimensions: {sorted(missing)}"
        )

    latitudes = field["latitude"].values
    longitudes = field["longitude"].values
    depths = field["depth"].values

    # Validate requested coordinates.
    if latitude < latitudes.min() or latitude > latitudes.max():
        raise ValueError("Latitude is outside the model domain.")

    if longitude < longitudes.min() or longitude > longitudes.max():
        raise ValueError("Longitude is outside the model domain.")

    if depth < depths.min() or depth > depths.max():
        raise ValueError("Depth is outside the model domain.")

    # Find surrounding latitude indices.
    lat_index = np.searchsorted(latitudes, latitude)

    lat_index = min(
        max(lat_index, 1),
        len(latitudes) - 1,
    )

    lat0 = latitudes[lat_index - 1]
    lat1 = latitudes[lat_index]

    # Find surrounding longitude indices.
    lon_index = np.searchsorted(longitudes, longitude)

    lon_index = min(
        max(lon_index, 1),
        len(longitudes) - 1,
    )

    lon0 = longitudes[lon_index - 1]
    lon1 = longitudes[lon_index]

    # Find surrounding depth indices.
    depth_index = np.searchsorted(depths, depth)

    depth_index = min(
        max(depth_index, 1),
        len(depths) - 1,
    )

    depth0 = depths[depth_index - 1]
    depth1 = depths[depth_index]

    # Retrieve the surrounding 2x2x2 voxel.
    values = field.isel(
        latitude=slice(lat_index - 1, lat_index + 1),
        longitude=slice(lon_index - 1, lon_index + 1),
        depth=slice(depth_index - 1, depth_index + 1),
    )

    if "time" in values.dims:
        values = values.isel(time=0)

    values = values.transpose("depth", "latitude", "longitude")

    cube = values.values

    if cube.shape != (2, 2, 2):
        raise ValueError(
            f"Expected 2x2x2 interpolation cube, got {cube.shape}."
        )

    if np.any(np.isnan(cube)):
        raise ValueError(
            "Cannot interpolate because one or more surrounding "
            "model values are invalid."
        )

    # Normalized interpolation coordinates.
    a = (latitude - lat0) / (lat1 - lat0)
    b = (longitude - lon0) / (lon1 - lon0)
    c = (depth - depth0) / (depth1 - depth0)

    # Trilinear interpolation.
    result = (
        cube[0, 0, 0] * (1 - a) * (1 - b) * (1 - c)
        + cube[0, 0, 1] * (1 - a) * b * (1 - c)
        + cube[0, 1, 0] * a * (1 - b) * (1 - c)
        + cube[0, 1, 1] * a * b * (1 - c)
        + cube[1, 0, 0] * (1 - a) * (1 - b) * c
        + cube[1, 0, 1] * (1 - a) * b * c
        + cube[1, 1, 0] * a * (1 - b) * c
        + cube[1, 1, 1] * a * b * c
    )

    return float(result)