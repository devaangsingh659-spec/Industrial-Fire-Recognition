from datetime import datetime, timezone

from backend.database.connection import (
    get_connection,
    release_connection
)


def get_fires_in_bbox(west, south, east, north):
    """
    Return only CURRENT thermal detections inside the
    requested bounding box.

    Main categories:

        NEW
            Latest observation is within the last 3 hours,
            with only one observation today and no previous-day
            observation.

        RECENT
            Exactly one observation today, older than 3 hours,
            with no previous-day observation.

        INTERMITTENT
            Multiple observations today, but no observation
            on a previous day.

        PERSISTENT
            Observed today and on at least one previous day
            within the 5-day persistence window.

    IMPORTANT:

        This function returns ONLY detections whose
        acquisition date is TODAY.

        Older detections are NOT returned by the main
        fire-search endpoint.

        Historical statistics for:
            - 15 days
            - 1 month
            - 2 months
            - 3 months

        will be handled separately.

    Database schema is not modified.

    Persistence analysis:
        - 500m spatial matching radius
        - 5-day historical window
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # ======================================================
        # CREATE BOUNDING BOX
        # ======================================================

        bbox = """
            ST_MakeEnvelope(
                %s,
                %s,
                %s,
                %s,
                4326
            )
        """

        # ======================================================
        # MAIN QUERY
        # ======================================================

        query = f"""
            SELECT

                d.id,

                ST_Y(d.geom) AS latitude,

                ST_X(d.geom) AS longitude,

                d.frp,

                d.brightness,

                d.acquisition_time,

                d.satellite,

                d.source,

                d.confidence,

                d.detection_type,

                d.prediction_status,

                MIN(h.acquisition_time) AS first_seen,

                MAX(h.acquisition_time) AS last_seen,

                COUNT(
                    DISTINCT h.acquisition_time
                ) AS observation_count,

                COUNT(
                    DISTINCT (
                        h.acquisition_time
                        AT TIME ZONE 'UTC'
                    )::date
                ) AS active_days,

                COUNT(
                    DISTINCT CASE
                        WHEN (
                            h.acquisition_time
                            AT TIME ZONE 'UTC'
                        )::date = (
                            d.acquisition_time
                            AT TIME ZONE 'UTC'
                        )::date
                        THEN h.acquisition_time
                    END
                ) AS today_observation_count,

                COUNT(
                    DISTINCT CASE
                        WHEN (
                            h.acquisition_time
                            AT TIME ZONE 'UTC'
                        )::date < (
                            d.acquisition_time
                            AT TIME ZONE 'UTC'
                        )::date
                        THEN (
                            h.acquisition_time
                            AT TIME ZONE 'UTC'
                        )::date
                    END
                ) AS previous_active_days

            FROM thermal_detections d

            LEFT JOIN thermal_detections h

                ON ST_DWithin(
                    d.geom::geography,
                    h.geom::geography,
                    500
                )

                AND h.acquisition_time >=
                    d.acquisition_time -
                    INTERVAL '5 days'

                AND h.acquisition_time <=
                    d.acquisition_time

            WHERE

                d.geom && {bbox}

                AND ST_Within(
                    d.geom,
                    {bbox}
                )

                -- Only today's detections are returned
                -- by the main fire-search endpoint.

                AND (
                    d.acquisition_time
                    AT TIME ZONE 'UTC'
                )::date = (
                    NOW()
                    AT TIME ZONE 'UTC'
                )::date

            GROUP BY

                d.id,

                d.geom,

                d.frp,

                d.brightness,

                d.acquisition_time,

                d.satellite,

                d.source,

                d.confidence,

                d.detection_type,

                d.prediction_status

            ORDER BY
                d.acquisition_time DESC;
        """

        # ======================================================
        # EXECUTE QUERY
        # ======================================================

        cursor.execute(
            query,
            (
                west,
                south,
                east,
                north,

                west,
                south,
                east,
                north
            )
        )

        rows = cursor.fetchall()

        # ======================================================
        # CURRENT UTC TIME
        # ======================================================

        now = datetime.now(timezone.utc)

        # ======================================================
        # BUILD RESPONSE
        # ======================================================

        detections = []

        for row in rows:

            # --------------------------------------------------
            # DATABASE VALUES
            # --------------------------------------------------

            detection_id = row[0]
            latitude = row[1]
            longitude = row[2]
            frp = row[3]
            brightness = row[4]
            acquisition_time = row[5]
            satellite = row[6]
            source = row[7]
            confidence = row[8]
            detection_type = row[9]
            prediction_status = row[10]

            first_seen_db = row[11]
            last_seen_db = row[12]
            observation_count_db = row[13]
            active_days_db = row[14]
            today_observation_count_db = row[15]
            previous_active_days_db = row[16]

            # --------------------------------------------------
            # NORMALIZE ACQUISITION TIME
            # --------------------------------------------------

            if acquisition_time is not None:

                if acquisition_time.tzinfo is None:
                    acquisition_time = acquisition_time.replace(
                        tzinfo=timezone.utc
                    )

                age = now - acquisition_time

                age_hours = (
                    age.total_seconds() / 3600.0
                )

            else:

                age_hours = 999999

            # --------------------------------------------------
            # SAFE COUNTS
            # --------------------------------------------------

            observation_count = (
                int(observation_count_db)
                if observation_count_db is not None
                else 0
            )

            active_days = (
                int(active_days_db)
                if active_days_db is not None
                else 0
            )

            today_observation_count = (
                int(today_observation_count_db)
                if today_observation_count_db is not None
                else 0
            )

            previous_active_days = (
                int(previous_active_days_db)
                if previous_active_days_db is not None
                else 0
            )

            # ==================================================
            # DEFAULT VALUES
            # ==================================================

            persistence_status = None
            persistence_score = None
            first_seen = None
            last_seen = None
            persistence_reason = None

            # ==================================================
            # PERSISTENT
            # ==================================================
            #
            # Detection exists today AND was observed on
            # at least one previous day.

            if previous_active_days >= 1:

                persistence_status = "PERSISTENT"

                first_seen = first_seen_db
                last_seen = last_seen_db

                persistence_reason = (
                    f"Detected today and across "
                    f"{previous_active_days} previous "
                    f"active day(s) within the 5-day "
                    f"analysis window."
                )

            # ==================================================
            # INTERMITTENT
            # ==================================================
            #
            # Multiple distinct observations today.
            #
            # No previous-day observation.

            elif today_observation_count >= 2:

                persistence_status = "INTERMITTENT"

                first_seen = first_seen_db
                last_seen = last_seen_db

                persistence_reason = (
                    f"Detected "
                    f"{today_observation_count} distinct "
                    f"times today with no observation "
                    f"on a previous day."
                )

            # ==================================================
            # NEW
            # ==================================================
            #
            # Very fresh satellite observation.
            #
            # Only one observation today.
            #
            # No previous-day history.

            elif (
                age_hours <= 3
                and today_observation_count == 1
                and previous_active_days == 0
            ):

                persistence_status = "NEW"

                first_seen = first_seen_db
                last_seen = last_seen_db

                persistence_reason = (
                    "Very recently detected by the satellite "
                    "within the last 3 hours with no repeated "
                    "observation yet."
                )

            # ==================================================
            # RECENT
            # ==================================================
            #
            # Exactly one observation today.
            #
            # Older than NEW threshold.
            #
            # No previous-day observation.

            elif (
                today_observation_count == 1
                and previous_active_days == 0
            ):

                persistence_status = "RECENT"

                first_seen = first_seen_db
                last_seen = last_seen_db

                persistence_reason = (
                    "Detected once during the current day "
                    "with no repeated observation yet."
                )

            # ==================================================
            # SAFETY FALLBACK
            # ==================================================

            else:

                persistence_status = "RECENT"

                first_seen = first_seen_db
                last_seen = last_seen_db

                persistence_reason = (
                    "Detected during the current day."
                )

            # ==================================================
            # PERSISTENCE SCORE
            # ==================================================

            persistence_score = min(
                active_days / 5.0,
                1.0
            )

            # ==================================================
            # BUILD RESPONSE
            # ==================================================

            detections.append({

                "id": detection_id,

                "latitude": (
                    float(latitude)
                    if latitude is not None
                    else None
                ),

                "longitude": (
                    float(longitude)
                    if longitude is not None
                    else None
                ),

                "frp": (
                    float(frp)
                    if frp is not None
                    else None
                ),

                "brightness": (
                    float(brightness)
                    if brightness is not None
                    else None
                ),

                "acquisition_time": acquisition_time,

                "satellite": satellite,

                "source": source,

                # ==================================================
                # ML FIELDS
                # ==================================================

                "confidence": (
                    float(confidence)
                    if confidence is not None
                    else None
                ),

                "detection_type": detection_type,

                "prediction_status": prediction_status,

                # ==================================================
                # PERSISTENCE FIELDS
                # ==================================================

                "persistence_status":
                    persistence_status,

                "persistence_score": (
                    round(
                        persistence_score,
                        3
                    )
                    if persistence_score is not None
                    else None
                ),

                "first_seen": first_seen,

                "last_seen": last_seen,

                "observation_count":
                    observation_count,

                "active_days":
                    active_days,

                "persistence_reason":
                    persistence_reason,

                # Main endpoint contains only current
                # detections, so this is always False.

                "is_historical": False
            })

        # ======================================================
        # LOGGING
        # ======================================================

        print("\n========================================")
        print("CURRENT FIRE SEARCH COMPLETE")
        print("========================================")

        print(
            "BBOX:",
            west,
            south,
            east,
            north
        )

        print(
            "Main detection window: TODAY ONLY"
        )

        print(
            "Persistence window: LAST 5 DAYS"
        )

        print(
            "Persistence radius: 500 meters"
        )

        print(
            "Detections returned:",
            len(detections)
        )

        # ======================================================
        # COUNTS
        # ======================================================

        persistent_count = sum(
            1
            for d in detections
            if d["persistence_status"] == "PERSISTENT"
        )

        intermittent_count = sum(
            1
            for d in detections
            if d["persistence_status"] == "INTERMITTENT"
        )

        recent_count = sum(
            1
            for d in detections
            if d["persistence_status"] == "RECENT"
        )

        new_count = sum(
            1
            for d in detections
            if d["persistence_status"] == "NEW"
        )

        # ======================================================
        # PRINT COUNTS
        # ======================================================

        print(
            "Persistent:",
            persistent_count
        )

        print(
            "Intermittent:",
            intermittent_count
        )

        print(
            "Recent:",
            recent_count
        )

        print(
            "New:",
            new_count
        )

        print(
            "Historical: NOT INCLUDED"
        )

        print("========================================\n")

        return detections

    except Exception as e:

        print("\n========================================")
        print("CURRENT FIRE SEARCH ERROR")
        print("========================================")

        print(
            "BBOX:",
            west,
            south,
            east,
            north
        )

        print(
            "ERROR:",
            e
        )

        print("========================================\n")

        raise

    finally:

        cursor.close()

        release_connection(conn)