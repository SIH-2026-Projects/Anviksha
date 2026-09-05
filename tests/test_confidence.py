from ocean_backend.science.confidence import calculate_confidence


def test_high_confidence():
    result = calculate_confidence(
        quality_flag="PASS",
        distance_km=2.0,
        depth_difference_m=5.0,
        time_difference_hours=3.0,
    )

    assert result == "HIGH"


def test_medium_confidence():
    result = calculate_confidence(
        quality_flag="PASS",
        distance_km=20.0,
        depth_difference_m=10.0,
        time_difference_hours=12.0,
    )

    assert result == "MEDIUM"


def test_low_confidence_bad_quality():
    result = calculate_confidence(
        quality_flag="FAIL",
        distance_km=2.0,
        depth_difference_m=5.0,
        time_difference_hours=3.0,
    )

    assert result == "LOW"


def test_low_confidence_large_distance():
    result = calculate_confidence(
        quality_flag="PASS",
        distance_km=100.0,
        depth_difference_m=5.0,
        time_difference_hours=3.0,
    )

    assert result == "LOW"


def test_low_confidence_large_time_difference():
    result = calculate_confidence(
        quality_flag="PASS",
        distance_km=2.0,
        depth_difference_m=5.0,
        time_difference_hours=48.0,
    )

    assert result == "LOW"
    
def test_suspect_observation_cannot_be_high_confidence():
    result = calculate_confidence(
        quality_flag="SUSPECT",
        distance_km=2.0,
        depth_difference_m=5.0,
        time_difference_hours=3.0,
    )

    assert result == "MEDIUM"


def test_fail_observation_is_always_low_confidence():
    result = calculate_confidence(
        quality_flag="FAIL",
        distance_km=1.0,
        depth_difference_m=0.0,
        time_difference_hours=0.0,
    )

    assert result == "LOW"