"""
Dataset Exporter for PostgreSQL / PostGIS
Extracts thermal detections and spatial boundaries to CSV, JSON, GeoJSON, or Parquet.

Usage:
    python export_dataset.py
    python export_dataset.py --format csv --output fires_dataset.csv
    python export_dataset.py --user postgres --password your_password --dbname industrial_fire_db
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def get_connection(host, port, dbname, user, password):
    """
    Connect to PostgreSQL using psycopg or psycopg2.
    """
    try:
        import psycopg
        conn = psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        return conn, "psycopg"
    except ImportError:
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password
            )
            return conn, "psycopg2"
        except ImportError:
            print("Error: Neither 'psycopg' nor 'psycopg2' is installed.")
            print("Please run: pip install psycopg[binary] or pip install psycopg2-binary")
            sys.exit(1)


def export_thermal_detections(conn, output_dir, export_format="csv"):
    """
    Query all thermal detections with latitude, longitude, and attributes.
    """
    import pandas as pd

    query = """
        SELECT
            id,
            ST_Y(geom) AS latitude,
            ST_X(geom) AS longitude,
            frp,
            brightness,
            acquisition_time,
            satellite,
            source,
            confidence,
            detection_type,
            prediction_status
        FROM thermal_detections
        ORDER BY acquisition_time DESC;
    """

    print("\n[1/2] Fetching thermal_detections from PostgreSQL...")
    try:
        df = pd.read_sql_query(query, conn)
        print(f" -> Successfully fetched {len(df)} detection records.")

        if df.empty:
            print(" [!] Note: 'thermal_detections' table is currently empty.")
            return df

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if export_format.lower() == "csv" or export_format.lower() == "all":
            csv_file = output_path / f"thermal_detections_{timestamp_str}.csv"
            df.to_csv(csv_file, index=False)
            print(f" -> Saved CSV to: {csv_file.resolve()}")

        if export_format.lower() == "json" or export_format.lower() == "all":
            json_file = output_path / f"thermal_detections_{timestamp_str}.json"
            df.to_json(json_file, orient="records", date_format="iso", indent=2)
            print(f" -> Saved JSON to: {json_file.resolve()}")

        if export_format.lower() == "geojson" or export_format.lower() == "all":
            try:
                import geopandas as gpd
                from shapely.geometry import Point

                geometry = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]
                gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
                geojson_file = output_path / f"thermal_detections_{timestamp_str}.geojson"
                gdf.to_file(geojson_file, driver="GeoJSON")
                print(f" -> Saved GeoJSON to: {geojson_file.resolve()}")
            except Exception as e:
                print(f" [!] GeoJSON export skipped (optional geopandas error: {e})")

        return df
    except Exception as e:
        print(f"Error extracting thermal_detections: {e}")
        return None


def export_spatial_boundaries(conn, output_dir, export_format="csv"):
    """
    Query spatial boundaries table if it exists.
    """
    import pandas as pd

    query = """
        SELECT
            id,
            source_type,
            ST_AsGeoJSON(geom) AS geometry_geojson
        FROM spatial_boundaries;
    """

    print("\n[2/2] Checking spatial_boundaries table...")
    try:
        df = pd.read_sql_query(query, conn)
        print(f" -> Successfully fetched {len(df)} boundary records.")

        if not df.empty:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(output_dir)
            if export_format.lower() in ("csv", "all"):
                csv_file = output_path / f"spatial_boundaries_{timestamp_str}.csv"
                df.to_csv(csv_file, index=False)
                print(f" -> Saved Boundaries CSV to: {csv_file.resolve()}")
            if export_format.lower() in ("json", "geojson", "all"):
                json_file = output_path / f"spatial_boundaries_{timestamp_str}.json"
                df.to_json(json_file, orient="records", indent=2)
                print(f" -> Saved Boundaries JSON to: {json_file.resolve()}")
        return df
    except Exception as e:
        print(f"Note: Could not query spatial_boundaries (may not exist yet): {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Export datasets from PostgreSQL database.")
    parser.add_argument("--host", default=os.getenv("DB_HOST", "localhost"), help="PostgreSQL host (default: localhost)")
    parser.add_argument("--port", default=os.getenv("DB_PORT", "5432"), help="PostgreSQL port (default: 5432)")
    parser.add_argument("--dbname", default=os.getenv("DB_NAME", "industrial_fire_db"), help="Database name (default: industrial_fire_db)")
    parser.add_argument("--user", default=os.getenv("DB_USER", "postgres"), help="Database user (default: postgres)")
    parser.add_argument("--password", default=os.getenv("DB_PASSWORD", ""), help="Database password")
    parser.add_argument("--format", choices=["csv", "json", "geojson", "all"], default="all", help="Export format (default: all)")
    parser.add_argument("--output-dir", default="./exported_data", help="Directory to save exported files (default: ./exported_data)")

    args = parser.parse_args()

    # Prompt for password if not provided and not in env
    password = args.password
    if not password:
        password = input(f"Enter PostgreSQL password for user '{args.user}': ")

    print("=" * 60)
    print("POSTGRESQL DATASET EXPORT UTILITY")
    print("=" * 60)
    print(f"Host: {args.host}:{args.port}")
    print(f"Database: {args.dbname}")
    print(f"User: {args.user}")
    print(f"Target Format: {args.format}")
    print(f"Output Directory: {Path(args.output_dir).resolve()}")
    print("=" * 60)

    try:
        conn, driver = get_connection(args.host, args.port, args.dbname, args.user, password)
        print(f"Connected to PostgreSQL successfully using {driver}!")

        export_thermal_detections(conn, args.output_dir, args.format)
        export_spatial_boundaries(conn, args.output_dir, args.format)

        conn.close()
        print("\n" + "=" * 60)
        print("EXPORT COMPLETED SUCCESSFULLY!")
        print(f"Check the folder: {Path(args.output_dir).resolve()}")
        print("=" * 60)
    except Exception as e:
        print(f"\n[X] Connection or Export Failed: {e}")
        print("\nTip: If authentication failed, ensure your password and database name are correct.")


if __name__ == "__main__":
    main()
