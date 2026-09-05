import numpy as np
import pytest

from ocean_backend.science.interpolation import linear_time, trilinear


def test_linear_time_midpoint():
    assert linear_time(10.0, 20.0, 0.5) == 15.0


def test_trilinear_constant_field():
    corners = np.full((2, 2, 2), 7.5)
    assert trilinear(corners, 0.2, 0.7, 0.4) == pytest.approx(7.5)


def test_trilinear_rejects_wrong_shape():
    try:
        trilinear(np.zeros((2, 2)), 0.5, 0.5, 0.5)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
def test_interpolate_3d_constant_field():
    import numpy as np
    import xarray as xr

    from ocean_backend.science.interpolation import interpolate_3d

    field = xr.DataArray(
        np.full((2, 2, 2), 10.0),
        dims=("depth", "latitude", "longitude"),
        coords={
            "depth": [0.0, 100.0],
            "latitude": [10.0, 20.0],
            "longitude": [60.0, 70.0],
        },
    )

    result = interpolate_3d(
        field,
        latitude=15.0,
        longitude=65.0,
        depth=50.0,
    )

    assert result == pytest.approx(10.0)