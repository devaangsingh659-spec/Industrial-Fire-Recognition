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
    """
    Extracts feature vector from fire detection dictionary with
    robust defaults for any missing or non-standard timestamp fields.
    """
    acq_time = detection.get("acquisition_time")
    if acq_time is not None:
        try:
            acquisition_time = pd.to_datetime(acq_time)
            hour = acquisition_time.hour
            month = acquisition_time.month
            day_of_week = acquisition_time.dayofweek
        except Exception:
            hour = 12
            month = 9
            day_of_week = 1
    else:
        hour = 12
        month = 9
        day_of_week = 1

    features = {
        "frp": float(detection.get("frp") if detection.get("frp") is not None else 20.0),
        "brightness": float(detection.get("brightness") if detection.get("brightness") is not None else 325.0),
        "latitude": float(detection.get("latitude") if detection.get("latitude") is not None else 0.0),
        "longitude": float(detection.get("longitude") if detection.get("longitude") is not None else 0.0),
        "hour": int(hour),
        "month": int(month),
        "day_of_week": int(day_of_week),
    }

    return pd.DataFrame(
        [features],
        columns=FEATURE_COLUMNS
    )