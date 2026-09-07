# backend/ml/train.py
"""
Model Training Script for Industrial Fire Recognition
Trains a Random Forest Classifier and Standard Scaler for classifying
satellite thermal detections into:
  - INDUSTRIAL (0)
  - AGRICULTURAL (1)
  - FOREST (2)
"""

import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS = [
    "frp",
    "brightness",
    "latitude",
    "longitude",
    "hour",
    "month",
    "day_of_week",
]

BASE_DIR = Path(__file__).resolve().parents[2]
MODELS_DIR = BASE_DIR / "models"


def normalize_probs(arr):
    p = np.array(arr, dtype=float)
    return p / p.sum()


def generate_synthetic_training_data(n_samples=3000, random_state=42):
    """
    Generates domain-calibrated synthetic training data reflecting real-world
    thermal detection characteristics:
      - Industrial: Continuous high/moderate FRP day & night, higher night brightness, consistent spots.
      - Agricultural: Daytime concentration (10am-4pm), moderate FRP, lower brightness, seasonal peak.
      - Forest: High/extreme FRP, intense brightness, active daytime/evening, high spread.
    """
    np.random.seed(random_state)
    records = []
    labels = []

    samples_per_class = n_samples // 3

    # 1. INDUSTRIAL (Class 0)
    for _ in range(samples_per_class):
        frp = np.random.gamma(shape=3.5, scale=12.0) + 15.0  # Steady moderate to high FRP (25 - 80+ MW)
        brightness = np.random.normal(loc=345.0, scale=18.0)  # High thermal signature (320 - 390 K)
        # Coordinates (clustered near industrial / urban zones)
        lat = np.random.uniform(low=-7.5, high=28.5)
        lon = np.random.uniform(low=70.0, high=120.0)
        hour = np.random.randint(0, 24)  # 24/7 operating flares/furnaces
        month = np.random.randint(1, 13)
        day_of_week = np.random.randint(0, 7)

        records.append([frp, brightness, lat, lon, hour, month, day_of_week])
        labels.append(0)

    # 2. AGRICULTURAL (Class 1)
    agri_month_p = normalize_probs([0.2, 0.2, 0.15, 0.15, 0.1, 0.05, 0.03, 0.03, 0.03, 0.02, 0.02, 0.02])
    for _ in range(samples_per_class):
        frp = np.random.gamma(shape=2.0, scale=6.0) + 3.0   # Lower to moderate FRP (5 - 25 MW)
        brightness = np.random.normal(loc=315.0, scale=12.0)  # Lower thermal signature (300 - 335 K)
        lat = np.random.uniform(low=-8.0, high=31.0)
        lon = np.random.uniform(low=72.0, high=118.0)
        # Peak during midday / afternoon stubble burning
        hour = int(np.clip(np.random.normal(loc=13.5, scale=2.5), 0, 23))
        # Peak in post-harvest months (April-May, Oct-Nov)
        month = np.random.choice([4, 5, 9, 10, 11, 12, 1, 2, 3, 6, 7, 8], p=agri_month_p)
        day_of_week = np.random.randint(0, 7)

        records.append([frp, brightness, lat, lon, hour, month, day_of_week])
        labels.append(1)

    # 3. FOREST (Class 2)
    forest_hour_p = normalize_probs([0.02]*6 + [0.04]*4 + [0.08]*8 + [0.04]*6)
    forest_month_p = normalize_probs([0.05, 0.12, 0.15, 0.15, 0.12, 0.06, 0.08, 0.10, 0.07, 0.04, 0.03, 0.03])
    for _ in range(samples_per_class):
        frp = np.random.gamma(shape=4.0, scale=20.0) + 20.0  # Large wild fires, high FRP (40 - 150+ MW)
        brightness = np.random.normal(loc=365.0, scale=22.0)  # Very high thermal radiance
        lat = np.random.uniform(low=-9.0, high=32.0)
        lon = np.random.uniform(low=68.0, high=125.0)
        # Active afternoon to night
        hour = np.random.choice(range(24), p=forest_hour_p)
        # Dry season peak (Feb-May, Jul-Sep)
        month = np.random.choice(range(1, 13), p=forest_month_p)
        day_of_week = np.random.randint(0, 7)

        records.append([frp, brightness, lat, lon, hour, month, day_of_week])
        labels.append(2)

    df = pd.DataFrame(records, columns=FEATURE_COLUMNS)
    y = np.array(labels)
    return df, y


def train_and_save_model():
    """Trains model and saves artifacts to models/ directory."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Generating training dataset...")
    X_df, y = generate_synthetic_training_data()

    print("Fitting StandardScaler...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_df)

    print("Training RandomForestClassifier...")
    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        min_samples_split=4,
        random_state=42,
        class_weight="balanced"
    )
    clf.fit(X_scaled, y)

    model_path = MODELS_DIR / "fire_classifier.pkl"
    scaler_path = MODELS_DIR / "scaler.pkl"

    joblib.dump(clf, model_path)
    joblib.dump(scaler, scaler_path)

    print(f"Model successfully saved to: {model_path}")
    print(f"Scaler successfully saved to: {scaler_path}")
    return clf, scaler


if __name__ == "__main__":
    train_and_save_model()
