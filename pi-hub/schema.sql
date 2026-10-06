-- Readings recorded from the MQTT state topic. One row per published
-- sample; the hub writes, nothing else does.
CREATE TABLE IF NOT EXISTS readings (
    id             INTEGER PRIMARY KEY,
    recorded_at    TEXT    NOT NULL,
    temperature_c  REAL,
    humidity_pct   REAL,
    pressure_hpa   REAL,
    rssi_dbm       INTEGER
);

-- Every query will be "readings in a time range", so the timestamp needs
-- an index of its own; the primary key only helps with insertion order.
CREATE INDEX IF NOT EXISTS idx_readings_recorded_at
    ON readings (recorded_at);