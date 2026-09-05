from fastapi import APIRouter, HTTPException

from backend.services.prediction_service import (
    classify_detection
)

router = APIRouter(
    prefix="/api/predictions",
    tags=["Predictions"]
)


@router.post("/{detection_id}")
def predict_detection(
    detection_id: int
):

    # TODO:
    # 1. Get detection from PostgreSQL
    # 2. Create features
    # 3. Run model
    # 4. Store prediction
    # 5. Return prediction

    return {
        "detection_id": detection_id,
        "status": "pending"
    }