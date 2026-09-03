CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS postgis;

-- Convert time-series tables to hypertables
-- The tables must be created first by Alembic/SQLAlchemy before this script runs.

SELECT create_hypertable('environmental_data', 'timestamp', if_not_exists => TRUE);
SELECT create_hypertable('water_quality_records', 'timestamp', if_not_exists => TRUE);
SELECT create_hypertable('intelligence_events', 'timestamp', if_not_exists => TRUE);
SELECT create_hypertable('audit_logs', 'timestamp', if_not_exists => TRUE);
SELECT create_hypertable('anomalies', 'timestamp', if_not_exists => TRUE);
