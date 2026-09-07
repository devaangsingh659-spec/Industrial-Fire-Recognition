from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DetectionFeatures(BaseModel):
    frp: float
    brightness: float
    latitude: float
    longitude: float
    acquisition_time: Optional[datetime] = None


class PredictionResponse(BaseModel):
    detection_id: Optional[int] = None
    status: str
    detection_type: Optional[str] = None
    confidence: Optional[float] = None
    prob_industrial: Optional[float] = None
    prob_agricultural: Optional[float] = None
    prob_forest: Optional[float] = None
    prediction_status: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
