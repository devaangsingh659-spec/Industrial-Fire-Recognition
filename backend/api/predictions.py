# backend/api/predictions.py

from fastapi import APIRouter, HTTPException

from backend.schemas.prediction import (
    DetectionFeatures,
    PredictionResponse
)
from backend.services.prediction_service import (
    classify_detection,
    predict_and_store_for_detection_id
)

router = APIRouter(
    prefix="/api/predictions",
    tags=["Predictions"]
)


@router.post("/classify", response_model=PredictionResponse)
def classify_ad_hoc(features: DetectionFeatures):
    """
    Perform on-the-fly ML classification and calculate class probabilities.
    """
    detection_dict = features.model_dump()
    result = classify_detection(detection_dict)
    return result


@router.post("/{detection_id}", response_model=PredictionResponse)
def predict_by_id(detection_id: int):
    """
    Predict and update classification for a specific detection in the database.
    """
    result = predict_and_store_for_detection_id(detection_id)
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=result.get("message"))
    elif result.get("status") == "failed":
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result