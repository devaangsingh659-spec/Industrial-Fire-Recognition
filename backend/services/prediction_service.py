# backend/services/prediction_service.py

from backend.ml.predictor import predict_fire
from backend.database.connection import get_connection, release_connection


def classify_detection(detection: dict) -> dict:
    """Classify a single detection object."""
    try:
        prediction = predict_fire(detection)
        return {
            "status": "completed",
            **prediction
        }
    except Exception as e:
        return {
            "status": "failed",
            "detection_type": "UNKNOWN",
            "confidence": 0.0,
            "prob_industrial": 0.0,
            "prob_agricultural": 0.0,
            "prob_forest": 0.0,
            "prediction_status": "FAILED",
            "error": str(e)
        }


def classify_detections_batch(detections: list[dict]) -> list[dict]:
    """Enrich a list of detection dictionaries with ML classification and probabilities."""
    enriched = []
    for d in detections:
        pred = classify_detection(d)
        enriched_d = dict(d)
        enriched_d["detection_type"] = pred.get("detection_type", "INDUSTRIAL")
        enriched_d["confidence"] = pred.get("confidence", 0.8)
        enriched_d["prediction_status"] = pred.get("prediction_status", "COMPLETED")
        enriched_d["prob_industrial"] = pred.get("prob_industrial", 0.33)
        enriched_d["prob_agricultural"] = pred.get("prob_agricultural", 0.33)
        enriched_d["prob_forest"] = pred.get("prob_forest", 0.34)
        enriched.append(enriched_d)
    return enriched


def predict_and_store_for_detection_id(detection_id: int) -> dict:
    """Fetch a detection by ID from PostgreSQL, compute prediction, update database, and return results."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                ST_Y(geom) as latitude,
                ST_X(geom) as longitude,
                frp,
                brightness,
                acquisition_time,
                satellite,
                source,
                confidence,
                detection_type,
                prediction_status
            FROM thermal_detections
            WHERE id = %s;
            """,
            (detection_id,)
        )
        row = cursor.fetchone()

        if not row:
            cursor.close()
            return {
                "detection_id": detection_id,
                "status": "not_found",
                "message": f"Detection with ID {detection_id} not found."
            }

        detection = {
            "id": row[0],
            "latitude": float(row[1]) if row[1] is not None else 0.0,
            "longitude": float(row[2]) if row[2] is not None else 0.0,
            "frp": float(row[3]) if row[3] is not None else 10.0,
            "brightness": float(row[4]) if row[4] is not None else 320.0,
            "acquisition_time": row[5],
            "satellite": row[6],
            "source": row[7]
        }

        prediction = predict_fire(detection)

        # Update in database
        try:
            cursor.execute(
                """
                UPDATE thermal_detections
                SET
                    detection_type = %s,
                    confidence = %s,
                    prediction_status = %s
                WHERE id = %s;
                """,
                (
                    prediction["detection_type"],
                    prediction["confidence"],
                    prediction["prediction_status"],
                    detection_id
                )
            )
            conn.commit()
        except Exception as db_err:
            print(f"Warning: Could not update DB for detection {detection_id}: {db_err}")

        cursor.close()

        return {
            "detection_id": detection_id,
            "status": "completed",
            **prediction
        }

    except Exception as e:
        return {
            "detection_id": detection_id,
            "status": "failed",
            "error": str(e)
        }
    finally:
        if conn:
            release_connection(conn)