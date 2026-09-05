# backend/ml/features.py

import pandas as pd


FEATURE_COLUMNS = [
    "frp",
    "brightness",
    "latitude",
    "longitude",
    "hour",
    "month",
    "day_of_week",
]


def create_features(detection: dict) -> pd.DataFrame:

    acquisition_time = pd.to_datetime(
        detection["acquisition_time"]
    )

    features = {
        "frp": detection["frp"],
        "brightness": detection["brightness"],
        "latitude": detection["latitude"],
        "longitude": detection["longitude"],

        "hour": acquisition_time.hour,

        "month": acquisition_time.month,

        "day_of_week": acquisition_time.dayofweek,
    }

    return pd.DataFrame(
        [features],
        columns=FEATURE_COLUMNS
    )