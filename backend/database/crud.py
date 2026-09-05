from backend.database.connection import get_connection


def get_detection_count():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM thermal_detections"
            )

            return cursor.fetchone()[0]

    finally:
        conn.close()


def get_detections_by_bbox(
    west,
    south,
    east,
    north
):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            query = """
                SELECT
                    id,
                    ST_Y(geom) AS latitude,
                    ST_X(geom) AS longitude,
                    frp,
                    brightness,
                    acquisition_time,
                    satellite,
                    instrument,
                    confidence,
                    daynight,
                    source
                FROM thermal_detections

                WHERE geom &&
                    ST_MakeEnvelope(
                        %s, %s, %s, %s, 4326
                    )

                AND ST_Within(
                    geom,
                    ST_MakeEnvelope(
                        %s, %s, %s, %s, 4326
                    )
                )

                ORDER BY acquisition_time DESC;
            """

            values = (
                west,
                south,
                east,
                north,
                west,
                south,
                east,
                north,
            )

            cursor.execute(query, values)

            rows = cursor.fetchall()

            columns = [
                "id",
                "latitude",
                "longitude",
                "frp",
                "brightness",
                "acquisition_time",
                "satellite",
                "instrument",
                "confidence",
                "daynight",
                "source",
            ]

            return [
                dict(zip(columns, row))
                for row in rows
            ]

    finally:
        conn.close()