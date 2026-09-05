from fastapi import APIRouter

from backend.database.connection import get_connection


router = APIRouter(
    prefix="/api/boundaries",
    tags=["Boundaries"]
)


@router.get("/")
def get_boundaries():

    conn = get_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    source_type,
                    ST_AsGeoJSON(geom)::json
                FROM spatial_boundaries;
                """
            )

            rows = cursor.fetchall()

            return {
                "boundaries": [
                    {
                        "id": row[0],
                        "source_type": row[1],
                        "geometry": row[2],
                    }
                    for row in rows
                ]
            }

    finally:
        conn.close()