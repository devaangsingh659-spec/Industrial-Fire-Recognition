# backend/ml/predictor.py

import numpy as np

from backend.ml.features import create_features
from backend.ml.model import (
    load_model,
    load_scaler
)


CLASS_NAMES = {
    0: "INDUSTRIAL",
    1: "AGRICULTURAL",
    2: "FOREST"
}


def predict_fire(detection: dict) -> dict:
    """
    Predict fire classification and individual class probabilities.
    Returns:
      detection_type: str ("INDUSTRIAL", "AGRICULTURAL", "FOREST")
      confidence: float (0.0 to 1.0)
      prob_industrial: float (0.0 to 1.0)
      prob_agricultural: float (0.0 to 1.0)
      prob_forest: float (0.0 to 1.0)
      prediction_status: str ("COMPLETED")
    """
    model = load_model()
    scaler = load_scaler()

    features = create_features(detection)
    X = scaler.transform(features)

    prediction = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]

    predicted_class = CLASS_NAMES.get(int(prediction), "INDUSTRIAL")

    prob_ind = float(probabilities[0]) if len(probabilities) > 0 else 0.333
    prob_agr = float(probabilities[1]) if len(probabilities) > 1 else 0.333
    prob_for = float(probabilities[2]) if len(probabilities) > 2 else 0.334

    max_prob = float(np.max(probabilities)) if len(probabilities) > 0 else 0.5

    return {
        "detection_type": predicted_class,
        "confidence": round(max_prob, 4),
        "prob_industrial": round(prob_ind, 4),
        "prob_agricultural": round(prob_agr, 4),
        "prob_forest": round(prob_for, 4),
        "prediction_status": "COMPLETED"
    }