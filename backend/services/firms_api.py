import os
from io import StringIO

import requests
import pandas as pd
import psycopg2
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

NASA_FIRMS_API_KEY = os.getenv("NASA_FIRMS_API_KEY")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# ------------------------------------------------------------
# IMPORTANT
#
# We continue fetching 5 days of FIRMS data because the
# previous 5 days are required to identify PERSISTENT fires.
#
# Old detections are NOT shown by the main fire-search API.
# They remain in the database for persistence analysis.
# ------------------------------------------------------------

DAYS = 5


# ============================================================
# NASA FIRMS SOURCES
# ============================================================

FIRMS_SOURCES = [
    "VIIRS_NOAA21_NRT",
    "VIIRS_NOAA20_NRT",
    "VIIRS_SNPP_NRT"
]


# ============================================================
# FETCH NASA FIRMS DATA
# ============================================================

def fetch_firms_data(
    source,
    west,
    south,
    east,
    north
):

    url = (
        "https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
        f"{NASA_FIRMS_API_KEY}/"
        f"{source}/"
        f"{west},{south},{east},{north}/"
        f"{DAYS}"
    )

    print("\n========================================")
    print(f"NASA FIRMS SOURCE: {source}")
    print("========================================")

    print(
        "Requested bounding box:",
        f"WEST={west}, SOUTH={south}, "
        f"EAST={east}, NORTH={north}"
    )

    print(
        "NASA URL:",
        url.replace(NASA_FIRMS_API_KEY, "***API_KEY***")
    )

    response = requests.get(
        url,
        timeout=60
    )

    print("HTTP Status:", response.status_code)

    if response.status_code != 200:

        print("NASA Response:")
        print(response.text)

    response.raise_for_status()

    df = pd.read_csv(
        StringIO(response.text)
    )

    if df.empty:

        print("NASA returned 0 detections.")

        return df


    # ========================================================
    # VERIFY ACTUAL NASA COORDINATES
    # ========================================================

    print("\nFIRST 5 NASA COORDINATES:")

    print(
        df[
            ["latitude", "longitude"]
        ].head()
    )

    print("\nNASA COORDINATE RANGE:")

    print(
        "Latitude:",
        df["latitude"].min(),
        "to",
        df["latitude"].max()
    )

    print(
        "Longitude:",
        df["longitude"].min(),
        "to",
        df["longitude"].max()
    )

    print(
        "\nNASA rows received:",
        len(df)
    )

    return df


# ============================================================
# CONNECT TO POSTGRESQL
# ============================================================

def get_db_connection():

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


# ============================================================
# CONVERT NASA DATE + TIME
# ============================================================

def convert_acquisition_time(row):

    acq_date = str(
        row["acq_date"]
    )

    acq_time = str(
        row["acq_time"]
    ).zfill(4)

    hour = int(
        acq_time[:2]
    )

    minute = int(
        acq_time[2:4]
    )

    # --------------------------------------------------------
    # NASA FIRMS acquisition times are UTC.
    #
    # Explicitly create a UTC-aware timestamp so PostgreSQL
    # TIMESTAMPTZ stores the observation correctly.
    # --------------------------------------------------------

    acquisition_time = pd.Timestamp(
        f"{acq_date} {hour:02d}:{minute:02d}:00",
        tz="UTC"
    )

    return acquisition_time.to_pydatetime()


# ============================================================
# INSERT / UPDATE POSTGIS
# ============================================================

def insert_into_postgis(
    df,
    source
):

    if df.empty:

        print(
            "No NASA detections to process."
        )

        return {
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }


    conn = get_db_connection()
    cursor = conn.cursor()

    inserted = 0
    updated = 0
    skipped = 0
    errors = 0


    for _, row in df.iterrows():

        try:

            # ------------------------------------------------
            # LATITUDE / LONGITUDE
            # ------------------------------------------------

            latitude = float(
                row["latitude"]
            )

            longitude = float(
                row["longitude"]
            )


            # ------------------------------------------------
            # BASIC COORDINATE VALIDATION
            # ------------------------------------------------

            if not (-90 <= latitude <= 90):

                raise ValueError(
                    f"Invalid latitude: {latitude}"
                )

            if not (-180 <= longitude <= 180):

                raise ValueError(
                    f"Invalid longitude: {longitude}"
                )


            # ------------------------------------------------
            # FRP
            # ------------------------------------------------

            frp = (
                float(row["frp"])
                if pd.notna(row["frp"])
                else None
            )


            # ------------------------------------------------
            # BRIGHTNESS
            # ------------------------------------------------

            brightness = (
                float(row["bright_ti4"])
                if pd.notna(row["bright_ti4"])
                else None
            )


            # ------------------------------------------------
            # SATELLITE
            # ------------------------------------------------

            satellite = (
                str(row["satellite"])
                if pd.notna(row["satellite"])
                else None
            )


            # ------------------------------------------------
            # SOURCE
            # ------------------------------------------------

            source_value = source


            # ------------------------------------------------
            # ACQUISITION TIME
            # ------------------------------------------------

            acquisition_time = convert_acquisition_time(
                row
            )


            # =================================================
            # CHECK FOR DUPLICATE
            # =================================================
            #
            # Same acquisition timestamp + within 100 metres
            # = same physical FIRMS detection.
            #
            # This prevents multiple FIRMS sources from creating
            # duplicate rows for the same satellite observation.
            #
            # IMPORTANT:
            # Different acquisition timestamps are NOT duplicates.
            # They are separate observations and are required for
            # INTERMITTENT / PERSISTENT analysis.
            # =================================================

            check_query = """

                SELECT id
                FROM thermal_detections

                WHERE acquisition_time = %s

                AND ST_DWithin(
                    geom::geography,

                    ST_SetSRID(
                        ST_MakePoint(%s, %s),
                        4326
                    )::geography,

                    100
                )

                LIMIT 1;

            """

            cursor.execute(
                check_query,
                (
                    acquisition_time,
                    longitude,
                    latitude
                )
            )

            existing = cursor.fetchone()


            # =================================================
            # EXISTING DETECTION
            # =================================================

            if existing:

                existing_id = existing[0]

                update_query = """

                    UPDATE thermal_detections

                    SET
                        satellite = COALESCE(
                            satellite,
                            %s
                        ),

                        source = COALESCE(
                            source,
                            %s
                        )

                    WHERE id = %s;

                """

                cursor.execute(
                    update_query,
                    (
                        satellite,
                        source_value,
                        existing_id
                    )
                )

                if cursor.rowcount > 0:

                    updated += 1

                else:

                    skipped += 1

                continue


            # =================================================
            # INSERT NEW DETECTION
            # =================================================
            #
            # confidence and detection_type remain NULL here.
            #
            # They are populated later by the ML pipeline.
            #
            # prediction_status is also left untouched here
            # because we are not changing the existing database
            # schema or forcing a new workflow into ingestion.
            # =================================================

            insert_query = """

                INSERT INTO thermal_detections
                (
                    geom,
                    frp,
                    brightness,
                    acquisition_time,
                    satellite,
                    source,
                    confidence,
                    detection_type
                )

                VALUES
                (
                    ST_SetSRID(
                        ST_MakePoint(%s, %s),
                        4326
                    ),

                    %s,
                    %s,
                    %s,
                    %s,
                    %s,

                    NULL,
                    NULL
                );

            """

            cursor.execute(
                insert_query,
                (
                    longitude,
                    latitude,
                    frp,
                    brightness,
                    acquisition_time,
                    satellite,
                    source_value
                )
            )

            inserted += 1


        except Exception as e:

            errors += 1

            print(
                "\n----------------------------------------"
            )

            print(
                "ERROR INSERTING DETECTION"
            )

            print(
                "----------------------------------------"
            )

            print(
                "Latitude:",
                row.get("latitude")
            )

            print(
                "Longitude:",
                row.get("longitude")
            )

            print(
                "Error:",
                e
            )


    # =========================================================
    # COMMIT
    # =========================================================

    conn.commit()

    cursor.close()
    conn.close()


    # =========================================================
    # RESULT
    # =========================================================

    print(
        "\n========================================"
    )

    print(
        "POSTGIS PROCESSING COMPLETE"
    )

    print(
        "========================================"
    )

    print(
        "Inserted:",
        inserted
    )

    print(
        "Updated:",
        updated
    )

    print(
        "Skipped duplicates:",
        skipped
    )

    print(
        "Errors:",
        errors
    )

    return {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "errors": errors
    }


# ============================================================
# PROCESS BOUNDING BOX
# ============================================================

def process_bounding_box(
    west,
    south,
    east,
    north
):

    # ========================================================
    # VALIDATE BOUNDING BOX
    # ========================================================

    if west >= east:

        raise ValueError(
            "Invalid bounding box: west must be smaller than east."
        )

    if south >= north:

        raise ValueError(
            "Invalid bounding box: south must be smaller than north."
        )

    if not (-180 <= west <= 180):

        raise ValueError(
            "West longitude must be between -180 and 180."
        )

    if not (-180 <= east <= 180):

        raise ValueError(
            "East longitude must be between -180 and 180."
        )

    if not (-90 <= south <= 90):

        raise ValueError(
            "South latitude must be between -90 and 90."
        )

    if not (-90 <= north <= 90):

        raise ValueError(
            "North latitude must be between -90 and 90."
        )


    print("\n")

    print(
        "===================================================="
    )

    print(
        "PROCESSING USER SELECTED BOUNDING BOX"
    )

    print(
        "===================================================="
    )

    print(
        "WEST :",
        west
    )

    print(
        "SOUTH:",
        south
    )

    print(
        "EAST :",
        east
    )

    print(
        "NORTH:",
        north
    )


    # ========================================================
    # TOTAL COUNTERS
    # ========================================================

    total_inserted = 0
    total_updated = 0
    total_skipped = 0
    total_errors = 0


    # ========================================================
    # PROCESS ALL NASA FIRMS SOURCES
    # ========================================================

    for source in FIRMS_SOURCES:

        try:

            # ------------------------------------------------
            # FETCH DATA
            # ------------------------------------------------

            df = fetch_firms_data(
                source,
                west,
                south,
                east,
                north
            )


            if df.empty:

                print(
                    f"No detections returned by {source}"
                )

                continue


            # ------------------------------------------------
            # DISPLAY SAMPLE
            # ------------------------------------------------

            print("\nSample data:")

            columns_to_show = [
                "latitude",
                "longitude",
                "frp",
                "bright_ti4",
                "acq_date",
                "acq_time",
                "satellite"
            ]

            available_columns = [
                column
                for column in columns_to_show
                if column in df.columns
            ]

            print(
                df[
                    available_columns
                ].head()
            )


            # ------------------------------------------------
            # INSERT / UPDATE
            # ------------------------------------------------

            result = insert_into_postgis(
                df,
                source
            )


            # ------------------------------------------------
            # ADD TO TOTALS
            # ------------------------------------------------

            total_inserted += result[
                "inserted"
            ]

            total_updated += result[
                "updated"
            ]

            total_skipped += result[
                "skipped"
            ]

            total_errors += result[
                "errors"
            ]


        except Exception as e:

            print(
                "\n========================================"
            )

            print(
                f"ERROR WITH {source}"
            )

            print(
                "========================================"
            )

            print(e)


    # ========================================================
    # FINAL RESULT
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        "FINAL RESULT"
    )

    print(
        "========================================"
    )

    print(
        "Total new detections inserted:",
        total_inserted
    )

    print(
        "Total existing detections updated:",
        total_updated
    )

    print(
        "Total duplicates skipped:",
        total_skipped
    )

    print(
        "Total errors:",
        total_errors
    )

    print(
        "========================================"
    )

    return {
        "inserted": total_inserted,
        "updated": total_updated,
        "skipped": total_skipped,
        "errors": total_errors
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # ENVIRONMENT VALIDATION
    # ========================================================

    if not NASA_FIRMS_API_KEY:

        raise ValueError(
            "NASA_FIRMS_API_KEY is missing from .env"
        )

    if not DB_NAME:

        raise ValueError(
            "DB_NAME is missing from .env"
        )

    if not DB_PASSWORD:

        raise ValueError(
            "DB_PASSWORD is missing from .env"
        )


    # ========================================================
    # DEFAULT TEST: INDIA
    #
    # This section is ONLY for running this file directly.
    #
    # Swagger/FastAPI should call process_bounding_box()
    # with the user's selected coordinates.
    # ========================================================

    process_bounding_box(
        west=68,
        south=6,
        east=97,
        north=37
    )