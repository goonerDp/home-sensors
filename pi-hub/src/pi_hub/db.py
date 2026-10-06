"""SQLite storage for sensor readings."""

import logging
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)

# Relative to the package root, which is two levels up from this file.
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sensors.db"
SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "schema.sql"


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Open the database, creating it from schema.sql if it is missing."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)

    # WAL lets a reader work while a writer is committing, instead of the
    # two blocking each other. It persists in the file, so setting it once
    # per connection is harmless.
    conn.execute("PRAGMA journal_mode=WAL")

    conn.executescript(SCHEMA_PATH.read_text())
    return conn


def insert_reading(conn: sqlite3.Connection, sample: dict) -> None:
    """Store one sample. The caller's timestamp is kept as-is."""
    conn.execute(
        """
        INSERT INTO readings
            (recorded_at, temperature_c, humidity_pct, pressure_hpa, rssi_dbm)
        VALUES
            (:timestamp, :temperature_c, :humidity_pct, :pressure_hpa, :rssi_dbm)
        """,
        sample,
    )
    conn.commit()