-- Water Quality Sensor Data
CREATE TABLE IF NOT EXISTS water_quality (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature FLOAT,
    tds_voltage FLOAT,
    uncompensated_tds FLOAT,
    compensated_tds FLOAT
);

-- Water Flow Sensor Data
CREATE TABLE IF NOT EXISTS water_flow (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    flowrate FLOAT,
    total_flow FLOAT,
    pressure FLOAT,
    pressure_voltage FLOAT
);

-- Water Level Sensor Data
CREATE TABLE IF NOT EXISTS water_level (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    water_level FLOAT,
    temperature FLOAT
);

-- Motor Sensor Data
CREATE TABLE IF NOT EXISTS motor (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20),
    voltage FLOAT,
    current FLOAT,
    power FLOAT,
    energy FLOAT,
    frequency FLOAT,
    power_factor FLOAT
);

-- Analyze Table (no analysis_id)
CREATE TABLE IF NOT EXISTS "analyze" (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50),
    result TEXT,
    state VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plan Table
CREATE TABLE IF NOT EXISTS plan (
    plan_id SERIAL PRIMARY KEY,
    node_id VARCHAR(50),
    command VARCHAR(100),
    parameters TEXT,
    priority INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Execute Table
CREATE TABLE IF NOT EXISTS execute (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50),
    result TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Table
CREATE TABLE IF NOT EXISTS knowledge (
    id SERIAL PRIMARY KEY,
    event TEXT,
    node_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Thresholds Table (dynamic parameters)
CREATE TABLE IF NOT EXISTS thresholds (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50),
    sensor_type VARCHAR(50),
    parameter VARCHAR(50),
    min_value FLOAT,
    max_value FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS nodes (
    node_id VARCHAR PRIMARY KEY
);