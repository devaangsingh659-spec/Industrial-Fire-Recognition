from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ==========================================================
# FIRE DETECTION RESPONSE MODEL
# ==========================================================

class FireDetection(BaseModel):

    # ------------------------------------------------------
    # BASIC IDENTIFICATION
    # ------------------------------------------------------

    id: int

    latitude: float
    longitude: float

    # ------------------------------------------------------
    # FIRMS OBSERVATION DATA
    # ------------------------------------------------------

    frp: Optional[float] = None
    brightness: Optional[float] = None

    acquisition_time: datetime

    satellite: Optional[str] = None
    source: Optional[str] = None

    # ------------------------------------------------------
    # ML CLASSIFICATION
    # ------------------------------------------------------

    confidence: Optional[float] = None

    detection_type: Optional[str] = None

    # Expected values:
    #
    #   INDUSTRIAL
    #   AGRICULTURAL
    #   OTHER
    #
    # Populated by the ML pipeline.

    # ------------------------------------------------------
    # ML PREDICTION STATUS
    # ------------------------------------------------------

    prediction_status: Optional[str] = None

    # Expected values:
    #
    #   PENDING
    #   PROCESSING
    #   COMPLETED
    #   FAILED

    # ------------------------------------------------------
    # PERSISTENCE / TEMPORAL CLASSIFICATION
    # ------------------------------------------------------

    persistence_status: Optional[str] = None

    # Expected values:
    #
    #   NEW
    #   RECENT
    #   INTERMITTENT
    #   PERSISTENT
    #
    # Only today's detections are returned by the main
    # fire search endpoint.

    persistence_score: Optional[float] = None

    # Score between 0 and 1.
    #
    # Calculated using the recent 5-day observation history.

    # ------------------------------------------------------
    # PERSISTENCE HISTORY
    # ------------------------------------------------------

    first_seen: Optional[datetime] = None

    last_seen: Optional[datetime] = None

    observation_count: Optional[int] = None

    active_days: Optional[int] = None

    # These values are calculated dynamically from the
    # recent observation history.

    # ------------------------------------------------------
    # EXPLANATION
    # ------------------------------------------------------

    persistence_reason: Optional[str] = None

    # Example:
    #
    # NEW:
    #   "First detected today within the last 3 hours."
    #
    # RECENT:
    #   "Detected once today."
    #
    # INTERMITTENT:
    #   "Detected multiple times today."
    #
    # PERSISTENT:
    #   "Detected today and on previous days."


# ==========================================================
# FIRE SEARCH RESPONSE
# ==========================================================

class FireSearchResponse(BaseModel):

    count: int

    detections: list[FireDetection]