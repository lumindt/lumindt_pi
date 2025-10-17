CREATE TABLE IF NOT EXISTS test_table (
    id SERIAL PRIMARY KEY,
    pi_id TEXT NOT NULL,
    test_id TEXT,
    voltage DOUBLE PRECISION,
    current DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    time TIMESTAMPTZ DEFAULT now()
);
