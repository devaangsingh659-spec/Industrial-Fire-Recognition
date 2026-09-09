import os
from dotenv import load_dotenv

load_dotenv()

FIRMS_MAP_KEY = os.getenv("NASA_FIRMS_API_KEY")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://{user}:{password}@{host}:{port}/{database}".format(
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "industrial_fire_db"),
    ),
)

FIRMS_SOURCE = os.getenv(
    "FIRMS_SOURCE",
    "VIIRS_NOAA21_NRT"
)

FIRMS_DAY_RANGE = int(
    os.getenv("FIRMS_DAY_RANGE", "1")
)


if not FIRMS_MAP_KEY:
    raise RuntimeError(
        "FIRMS_MAP_KEY is missing from .env"
    )

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing from .env"
    )