# backend/ml/preprocessing.py

import joblib


MODEL_PATH = "models/fire_classifier.pkl"
SCALER_PATH = "models/scaler.pkl"


def load_model():

    return joblib.load(
        MODEL_PATH
    )


def load_scaler():

    return joblib.load(
        SCALER_PATH
    )