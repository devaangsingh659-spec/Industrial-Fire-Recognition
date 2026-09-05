# backend/ml/model.py

from pathlib import Path
import joblib


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    BASE_DIR /
    "models" /
    "fire_classifier.pkl"
)

SCALER_PATH = (
    BASE_DIR /
    "models" /
    "scaler.pkl"
)


_model = None
_scaler = None


def load_model():

    global _model

    if _model is None:

        _model = joblib.load(
            MODEL_PATH
        )

    return _model


def load_scaler():

    global _scaler

    if _scaler is None:

        _scaler = joblib.load(
            SCALER_PATH
        )

    return _scaler