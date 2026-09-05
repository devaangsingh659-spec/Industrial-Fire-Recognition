def validate_bbox(
    west: float,
    south: float,
    east: float,
    north: float,
):

    if not -180 <= west <= 180:
        raise ValueError(
            "West longitude must be between -180 and 180."
        )

    if not -180 <= east <= 180:
        raise ValueError(
            "East longitude must be between -180 and 180."
        )

    if not -90 <= south <= 90:
        raise ValueError(
            "South latitude must be between -90 and 90."
        )

    if not -90 <= north <= 90:
        raise ValueError(
            "North latitude must be between -90 and 90."
        )

    if west >= east:
        raise ValueError(
            "West must be smaller than east."
        )

    if south >= north:
        raise ValueError(
            "South must be smaller than north."
        )

    return True