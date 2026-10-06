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
-- an index of its own. UNIQUE also makes the insert idempotent: the hub
-- republishes its last sample as a retained message, so a recorder
-- restart would otherwise store the same reading twice.
CREATE UNIQUE INDEX IF NOT EXISTS idx_readings_recorded_at
    ON readings (recorded_at);