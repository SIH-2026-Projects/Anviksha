import numpy as np
import pytest

from ocean_backend.science.comparison import bias, difference, mae, rmse


def test_difference_is_model_minus_observation():
    assert difference(19.82, 18.91) == pytest.approx(0.91)


def test_basic_statistics():
    model = np.array([2.0, 4.0])
    obs = np.array([1.0, 3.0])
    assert bias(model, obs) == 1.0
    assert mae(model, obs) == 1.0
    assert rmse(model, obs) == 1.0
