from backend.ml.predictor import predict_fire


def classify_detection(detection):

    try:

        prediction = predict_fire(
            detection
        )

        return {
            "status": "completed",
            **prediction
        }

    except Exception as e:

        return {
            "status": "failed",
            "error": str(e)
        }