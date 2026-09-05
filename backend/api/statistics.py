from fastapi import APIRouter

from backend.database.connection import get_connection


router = APIRouter(
    prefix="/api/statistics",
    tags=["Statistics"]
)


@router.get("/")
def get_statistics():

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    COUNT(*),
                    COALESCE(SUM(frp), 0),
                    MAX(acquisition_time)
                FROM thermal_detections;
                """
            )

            row = cursor.fetchone()

            return {
                "total_detections": row[0],
                "total_frp": float(row[1]),
                "latest_detection": row[2],
            }

    finally:
        conn.close()