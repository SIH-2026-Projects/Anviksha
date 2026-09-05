from datetime import datetime


def time_difference_hours(
    time1: datetime,
    time2: datetime,
) -> float:
    """
    Calculate the absolute time difference between two timestamps.

    Returns:
        Difference in hours.
    """

    difference = abs(time1 - time2)

    return difference.total_seconds() / 3600.0