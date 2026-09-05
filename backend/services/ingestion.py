import pandas as pd

from psycopg2.extras import execute_values

from backend.database.connection import (
    get_connection,
    release_connection
)


# ==========================================================
# CONFIGURATION
# ==========================================================

# Two detections are considered duplicates when:
#
#   1. acquisition_time is exactly the same
#   2. location is within 100 meters
#
# Different acquisition times are preserved because they are
# required for persistence analysis.
DUPLICATE_RADIUS_METERS = 100


def insert_detections(df, source):
    """
    Insert NASA FIRMS detections into PostgreSQL/PostGIS.

    Responsibilities:
        1. Validate and clean FIRMS data
        2. Convert acquisition time to UTC
        3. Remove duplicate rows inside the NASA response
        4. Load data into a temporary staging table
        5. Insert only genuinely new observations
        6. Mark newly inserted detections as PENDING

    Persistence classification is handled separately.

    Historical observations remain in the database because
    they are required to determine PERSISTENT detections.
    """

    # ==========================================================
    # EMPTY DATA CHECK
    # ==========================================================

    if df is None or df.empty:

        print(
            "No detections to insert."
        )

        return 0


    print(
        "\n========================================"
    )

    print(
        "DATABASE INGESTION"
    )

    print(
        "========================================"
    )

    print(
        "NASA rows received:",
        len(df)
    )


    # ==========================================================
    # 1. COPY DATA
    # ==========================================================

    data = df.copy()


    # ==========================================================
    # 2. CONVERT NUMERICAL FIELDS
    # ==========================================================

    data["latitude"] = pd.to_numeric(
        data["latitude"],
        errors="coerce"
    )

    data["longitude"] = pd.to_numeric(
        data["longitude"],
        errors="coerce"
    )

    data["frp"] = pd.to_numeric(
        data["frp"],
        errors="coerce"
    )

    data["bright_ti4"] = pd.to_numeric(
        data["bright_ti4"],
        errors="coerce"
    )


    # ==========================================================
    # 3. REMOVE INVALID COORDINATES
    # ==========================================================

    data = data.dropna(
        subset=[
            "latitude",
            "longitude"
        ]
    )

    data = data[
        (data["latitude"] >= -90) &
        (data["latitude"] <= 90) &
        (data["longitude"] >= -180) &
        (data["longitude"] <= 180)
    ]


    # ==========================================================
    # 4. CREATE ACQUISITION TIME
    # ==========================================================
    #
    # NASA FIRMS acq_date + acq_time are UTC.
    #
    # Example:
    #
    #   2026-09-04 + 1735
    #
    # becomes:
    #
    #   2026-09-04 17:35:00+00:00
    #
    # utc=True ensures that PostgreSQL receives the timestamp
    # as an absolute point in time.
    # ==========================================================

    data["acquisition_time"] = pd.to_datetime(
        data["acq_date"].astype(str)
        + " "
        + data["acq_time"].astype(str).str.zfill(4),
        errors="coerce",
        utc=True
    )

    data = data.dropna(
        subset=[
            "acquisition_time"
        ]
    )


    # ==========================================================
    # 5. NORMALIZE SATELLITE
    # ==========================================================

    data["satellite"] = (
        data["satellite"]
        .astype(str)
        .str.strip()
    )

    data = data[
        data["satellite"].notna() &
        (data["satellite"] != "") &
        (data["satellite"].str.lower() != "nan")
    ]


    # ==========================================================
    # 6. REMOVE DUPLICATES INSIDE NASA RESPONSE
    # ==========================================================
    #
    # Same:
    #   latitude
    #   longitude
    #   acquisition_time
    #   satellite
    #
    # = duplicate row in the same NASA response.
    #
    # Different acquisition times remain separate.
    # ==========================================================

    data = data.drop_duplicates(
        subset=[
            "latitude",
            "longitude",
            "acquisition_time",
            "satellite"
        ]
    )


    print(
        "Valid rows:",
        len(data)
    )


    # ==========================================================
    # 7. DEBUG: SHOW NASA OBSERVATION TIMES
    # ==========================================================
    #
    # This helps verify whether NASA is returning observations
    # from today or from previous days.
    # ==========================================================

    print(
        "\nNASA ACQUISITION TIMES:"
    )

    print(
        data[
            [
                "latitude",
                "longitude",
                "acquisition_time",
                "satellite"
            ]
        ].to_string(index=False)
    )


    if data.empty:

        print(
            "No valid data."
        )

        return 0


    # ==========================================================
    # 8. SHOW DATE DISTRIBUTION
    # ==========================================================

    print(
        "\nNASA OBSERVATION DATE DISTRIBUTION:"
    )

    date_distribution = (
        data["acquisition_time"]
        .dt.date
        .value_counts()
        .sort_index()
    )

    for detection_date, count in date_distribution.items():

        print(
            f"{detection_date}: {count}"
        )


    # ==========================================================
    # 9. CREATE ROW LIST
    # ==========================================================

    rows = []

    for row in data.itertuples(
        index=False
    ):

        # ------------------------------------------------------
        # FRP
        # ------------------------------------------------------

        frp = (
            float(row.frp)
            if pd.notna(row.frp)
            else None
        )


        # ------------------------------------------------------
        # BRIGHTNESS
        # ------------------------------------------------------

        brightness = (
            float(row.bright_ti4)
            if pd.notna(row.bright_ti4)
            else None
        )


        # ------------------------------------------------------
        # ACQUISITION TIME
        # ------------------------------------------------------

        acquisition_time = (
            row.acquisition_time.to_pydatetime()
        )


        rows.append(
            (
                float(row.latitude),
                float(row.longitude),
                frp,
                brightness,
                acquisition_time,
                str(row.satellite),
                str(source)
            )
        )


    # ==========================================================
    # 10. GET DATABASE CONNECTION
    # ==========================================================

    conn = get_connection()

    cursor = conn.cursor()


    try:

        # ======================================================
        # 11. CREATE TEMPORARY STAGING TABLE
        # ======================================================

        cursor.execute(
            """
            CREATE TEMP TABLE firms_staging (
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                frp DOUBLE PRECISION,
                brightness DOUBLE PRECISION,
                acquisition_time TIMESTAMPTZ,
                satellite TEXT,
                source TEXT
            )
            ON COMMIT DROP;
            """
        )


        # ======================================================
        # 12. LOAD DATA INTO STAGING
        # ======================================================

        print(
            "\nLoading rows into staging table..."
        )

        execute_values(
            cursor,
            """
            INSERT INTO firms_staging
            (
                latitude,
                longitude,
                frp,
                brightness,
                acquisition_time,
                satellite,
                source
            )
            VALUES %s
            """,
            rows,
            page_size=5000
        )

        print(
            "Staging complete:",
            len(rows),
            "rows"
        )


        # ======================================================
        # 13. INSERT NEW DETECTIONS
        # ======================================================
        #
        # Duplicate condition:
        #
        #   SAME acquisition timestamp
        #   AND
        #   WITHIN 100 meters
        #
        # Satellite/source are intentionally NOT included.
        #
        # Therefore:
        #
        # Same location + same time
        # from NOAA-20 and SNPP
        # -> one database observation.
        #
        # Same location + different time
        # -> new observation.
        #
        # This is necessary for:
        #
        #   NEW
        #   RECENT
        #   INTERMITTENT
        #   PERSISTENT
        # ======================================================

        print(
            "Checking duplicates..."
        )

        cursor.execute(
            """
            INSERT INTO thermal_detections
            (
                geom,
                frp,
                brightness,
                acquisition_time,
                satellite,
                source,
                confidence,
                detection_type,
                prediction_status
            )

            SELECT
                ST_SetSRID(
                    ST_MakePoint(
                        s.longitude,
                        s.latitude
                    ),
                    4326
                ),

                s.frp,

                s.brightness,

                s.acquisition_time,

                s.satellite,

                s.source,

                NULL,

                NULL,

                'PENDING'

            FROM firms_staging s

            WHERE NOT EXISTS (

                SELECT 1

                FROM thermal_detections t

                WHERE
                    t.acquisition_time = s.acquisition_time

                    AND ST_DWithin(
                        t.geom::geography,

                        ST_SetSRID(
                            ST_MakePoint(
                                s.longitude,
                                s.latitude
                            ),
                            4326
                        )::geography,

                        %s
                    )
            );
            """,
            (
                DUPLICATE_RADIUS_METERS,
            )
        )


        inserted = cursor.rowcount


        # ======================================================
        # 14. CALCULATE SKIPPED ROWS
        # ======================================================

        skipped = max(
            0,
            len(rows) - inserted
        )


        # ======================================================
        # 15. COMMIT
        # ======================================================

        conn.commit()


        # ======================================================
        # 16. FINAL LOGGING
        # ======================================================

        print(
            "\n========================================"
        )

        print(
            "DATABASE INSERT COMPLETE"
        )

        print(
            "========================================"
        )

        print(
            "Processed:",
            len(rows)
        )

        print(
            "Inserted:",
            inserted
        )

        print(
            "Skipped duplicates:",
            skipped
        )

        print(
            "Errors:",
            0
        )

        print(
            "========================================"
        )


        return inserted


    except Exception as e:

        conn.rollback()

        print(
            "\nDATABASE ERROR:"
        )

        print(
            e
        )

        raise


    finally:

        cursor.close()

        # Return connection to the pool.
        release_connection(
            conn
        )