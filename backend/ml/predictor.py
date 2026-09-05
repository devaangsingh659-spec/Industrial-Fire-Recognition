# backend/ml/predictor.py

import numpy as np

from backend.ml.features import create_features
from backend.ml.model import (
    load_model,
    load_scaler
)


CLASS_NAMES = {
    0: "industrial",
    1: "agricultural",
    2: "forest"
}


def predict_fire(detection: dict):

    model = load_model()

    scaler = load_scaler()


    features = create_features(
        detection
    )


    X = scaler.transform(
        features
    )


    prediction = model.predict(
        X
    )[0]


    probabilities = (
        model.predict_proba(X)[0]
    )


    predicted_class = CLASS_NAMES[
        int(prediction)
    ]


    return {

        "detection_type":
            predicted_class,

        "prob_industrial":
            float(probabilities[0]),

        "prob_agricultural":
            float(probabilities[1]),

        "prob_forest":
            float(probabilities[2]),

        "confidence":
            float(np.max(probabilities))
    }