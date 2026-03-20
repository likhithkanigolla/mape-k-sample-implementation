-- Complete Database Setup for IoT MAPE-K System
-- Run this to create all required tables for the system
-- Database: mapek_dt (or iot_mapek - update iot_gateway.py if using mapek_dt)

-- ============================================================================
-- SENSOR DATA TABLES (Store incoming IoT sensor data)
-- ============================================================================

-- Water Quality Sensor Data
CREATE TABLE IF NOT EXISTS water_quality (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    temperature FLOAT NOT NULL,
    tds_voltage FLOAT NOT NULL,
    uncompensated_tds FLOAT NOT NULL,
    compensated_tds FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT water_quality_node_id_check CHECK (node_id != '')
);

CREATE INDEX IF NOT EXISTS idx_water_quality_node_id ON water_quality(node_id);
CREATE INDEX IF NOT EXISTS idx_water_quality_timestamp ON water_quality(timestamp DESC);

-- Water Level Sensor Data
CREATE TABLE IF NOT EXISTS water_level (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    water_level FLOAT NOT NULL,
    temperature FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT water_level_node_id_check CHECK (node_id != '')
);

CREATE INDEX IF NOT EXISTS idx_water_level_node_id ON water_level(node_id);
CREATE INDEX IF NOT EXISTS idx_water_level_timestamp ON water_level(timestamp DESC);

-- Water Flow Sensor Data
CREATE TABLE IF NOT EXISTS water_flow (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    flowrate FLOAT NOT NULL,
    total_flow FLOAT NOT NULL,
    pressure FLOAT NOT NULL,
    pressure_voltage FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT water_flow_node_id_check CHECK (node_id != '')
);

CREATE INDEX IF NOT EXISTS idx_water_flow_node_id ON water_flow(node_id);
CREATE INDEX IF NOT EXISTS idx_water_flow_timestamp ON water_flow(timestamp DESC);

-- Motor Sensor Data
CREATE TABLE IF NOT EXISTS motor (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    status VARCHAR(10) NOT NULL,
    voltage FLOAT NOT NULL,
    current FLOAT NOT NULL,
    power FLOAT NOT NULL,
    energy FLOAT NOT NULL,
    frequency FLOAT NOT NULL,
    power_factor FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT motor_node_id_check CHECK (node_id != ''),
    CONSTRAINT motor_status_check CHECK (status IN ('ON', 'OFF'))
);

CREATE INDEX IF NOT EXISTS idx_motor_node_id ON motor(node_id);
CREATE INDEX IF NOT EXISTS idx_motor_timestamp ON motor(timestamp DESC);

-- ============================================================================
-- MAPE-K CONFIGURATION TABLES (Rules and thresholds)
-- ============================================================================

-- Nodes Registry (Optional - for tracking registered nodes)
CREATE TABLE IF NOT EXISTS nodes (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) UNIQUE NOT NULL,
    node_type VARCHAR(50) NOT NULL,
    ip_address VARCHAR(50),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_nodes_node_id ON nodes(node_id);

-- Thresholds for Anomaly Detection
CREATE TABLE IF NOT EXISTS thresholds (
    id SERIAL PRIMARY KEY,
    parameter VARCHAR(100) NOT NULL,
    min_value FLOAT,
    max_value FLOAT,
    description TEXT,
    CONSTRAINT thresholds_parameter_unique UNIQUE (parameter)
);

CREATE INDEX IF NOT EXISTS idx_thresholds_parameter ON thresholds(parameter);

-- Action Plans for Different States
CREATE TABLE IF NOT EXISTS plans (
    id SERIAL PRIMARY KEY,
    state VARCHAR(50) NOT NULL,
    plan_code VARCHAR(100) NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 1,
    CONSTRAINT plans_unique UNIQUE (state, plan_code)
);

CREATE INDEX IF NOT EXISTS idx_plans_state ON plans(state);
CREATE INDEX IF NOT EXISTS idx_plans_priority ON plans(priority DESC);

-- ============================================================================
-- MAPE-K EXECUTION LOGGING TABLES (Track MAPE-K loop operations)
-- ============================================================================

-- Analyze Results Log
-- Note: 'analyze' is a reserved keyword in PostgreSQL, so we use quotes
CREATE TABLE IF NOT EXISTS "analyze" (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    result TEXT,
    state VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analyze_node_id ON "analyze"(node_id);
CREATE INDEX IF NOT EXISTS idx_analyze_timestamp ON "analyze"(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_analyze_state ON "analyze"(state);

-- Plan Selection Log
CREATE TABLE IF NOT EXISTS plan_selection (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    plan_code VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_plan_selection_node_id ON plan_selection(node_id);
CREATE INDEX IF NOT EXISTS idx_plan_selection_timestamp ON plan_selection(timestamp DESC);

-- Execution Results Log
CREATE TABLE IF NOT EXISTS execution (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    plan_code VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_execution_node_id ON execution(node_id);
CREATE INDEX IF NOT EXISTS idx_execution_timestamp ON execution(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_execution_status ON execution(status);

-- ============================================================================
-- IOT GATEWAY EXECUTION LOG (Commands sent to devices)
-- ============================================================================

-- Execution log for IoT Gateway command routing
CREATE TABLE IF NOT EXISTS execution_log (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    plan_code VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL,  -- 'success' or 'failed'
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_execution_log_node_id ON execution_log(node_id);
CREATE INDEX IF NOT EXISTS idx_execution_log_timestamp ON execution_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_execution_log_status ON execution_log(status);

-- ============================================================================
-- INSERT DEFAULT CONFIGURATION DATA
-- ============================================================================

-- Insert default thresholds
INSERT INTO thresholds (parameter, min_value, max_value, description) VALUES
    ('temperature', 15.0, 35.0, 'Normal water temperature range (°C)'),
    ('tds_voltage', 0.0, 3.0, 'Normal TDS voltage range (V)'),
    ('uncompensated_tds', 0.0, 600.0, 'Normal uncompensated TDS range (ppm)'),
    ('compensated_tds', 0.0, 600.0, 'Normal compensated TDS range (ppm)'),
    ('water_level', 0.0, 15.0, 'Normal water level range (cm)'),
    ('flowrate', 0.0, 15.0, 'Normal flow rate range (L/min)'),
    ('total_flow', 0.0, 2000.0, 'Normal total flow range (L)'),
    ('pressure', 0.0, 6.0, 'Normal pressure range (bar)'),
    ('pressure_voltage', 0.0, 3.0, 'Normal pressure voltage range (V)'),
    ('voltage', 210.0, 250.0, 'Normal motor voltage range (V)'),
    ('current', 0.0, 12.0, 'Normal motor current range (A)'),
    ('power', 0.0, 2100.0, 'Normal motor power range (W)'),
    ('energy', 0.0, 120.0, 'Normal motor energy range (kWh)'),
    ('frequency', 48.0, 52.0, 'Normal motor frequency range (Hz)'),
    ('power_factor', 0.75, 1.0, 'Normal motor power factor range')
ON CONFLICT (parameter) DO NOTHING;

-- Insert default action plans
INSERT INTO plans (state, plan_code, description, priority) VALUES
    ('NORMAL', 'NO_ACTION', 'System operating normally', 1),
    ('HIGH_TEMPERATURE', 'ACTIVATE_COOLING', 'Activate cooling system', 1),
    ('HIGH_TDS', 'RECALIBRATE_SENSOR', 'Recalibrate TDS sensor', 1),
    ('HIGH_TDS_VOLTAGE', 'RECALIBRATE_SENSOR', 'Recalibrate TDS voltage sensor', 1),
    ('LOW_WATER_LEVEL', 'ACTIVATE_PUMP', 'Activate water pump', 1),
    ('HIGH_WATER_LEVEL', 'STOP_PUMP', 'Stop water pump', 1),
    ('HIGH_FLOW_RATE', 'REDUCE_VALVE_OPENING', 'Reduce valve opening', 1),
    ('LOW_FLOW_RATE', 'INCREASE_VALVE_OPENING', 'Increase valve opening', 1),
    ('HIGH_PRESSURE', 'REDUCE_PUMP_SPEED', 'Reduce pump speed', 1),
    ('LOW_VOLTAGE', 'CHECK_POWER_SUPPLY', 'Check power supply', 1),
    ('HIGH_CURRENT', 'REDUCE_MOTOR_LOAD', 'Reduce motor load', 1),
    ('LOW_FREQUENCY', 'CHECK_POWER_GRID', 'Check power grid frequency', 1),
    ('LOW_POWER_FACTOR', 'INSTALL_CAPACITOR', 'Install power factor correction capacitor', 2),
    ('ANOMALY', 'RECALIBRATE_SENSOR', 'Recalibrate sensor and check connections', 1),
    ('CRITICAL', 'EMERGENCY_SHUTDOWN', 'Emergency system shutdown', 1)
ON CONFLICT (state, plan_code) DO NOTHING;

-- Insert default nodes (optional - for reference)
INSERT INTO nodes (node_id, node_type, ip_address, description) VALUES
    ('water_quality_1', 'water_quality', 'localhost:8001', 'Water Quality Sensor Node 1'),
    ('water_level_1', 'water_level', 'localhost:8002', 'Water Level Sensor Node 1'),
    ('water_flow_1', 'water_flow', 'localhost:8003', 'Water Flow Sensor Node 1'),
    ('motor_1', 'motor', 'localhost:8004', 'Motor Sensor Node 1')
ON CONFLICT (node_id) DO NOTHING;

-- ============================================================================
-- USEFUL VIEWS FOR MONITORING
-- ============================================================================

-- View for recent sensor readings
CREATE OR REPLACE VIEW recent_sensor_data AS
SELECT 'water_quality' as sensor_type, node_id, timestamp, 
       temperature, tds_voltage as value1, uncompensated_tds as value2
FROM water_quality
WHERE timestamp > NOW() - INTERVAL '1 hour'
UNION ALL
SELECT 'water_level' as sensor_type, node_id, timestamp,
       temperature, water_level as value1, NULL as value2
FROM water_level
WHERE timestamp > NOW() - INTERVAL '1 hour'
UNION ALL
SELECT 'water_flow' as sensor_type, node_id, timestamp,
       NULL as temperature, flowrate as value1, pressure as value2
FROM water_flow
WHERE timestamp > NOW() - INTERVAL '1 hour'
UNION ALL
SELECT 'motor' as sensor_type, node_id, timestamp,
       NULL as temperature, voltage as value1, current as value2
FROM motor
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;

-- View for recent MAPE-K executions
CREATE OR REPLACE VIEW recent_executions AS
SELECT 
    node_id,
    plan_code,
    description,
    status,
    timestamp
FROM execution_log
ORDER BY timestamp DESC
LIMIT 100;

-- View for execution statistics
CREATE OR REPLACE VIEW execution_stats AS
SELECT 
    node_id,
    COUNT(*) as total_executions,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
    MAX(timestamp) as last_execution
FROM execution_log
GROUP BY node_id;

-- View for MAPE-K loop statistics
CREATE OR REPLACE VIEW mapek_stats AS
SELECT 
    'analyze' as component,
    COUNT(*) as operations,
    COUNT(DISTINCT node_id) as unique_nodes,
    MAX(timestamp) as last_operation
FROM "analyze"
UNION ALL
SELECT 
    'plan' as component,
    COUNT(*) as operations,
    COUNT(DISTINCT node_id) as unique_nodes,
    MAX(timestamp) as last_operation
FROM plan_selection
UNION ALL
SELECT 
    'execute' as component,
    COUNT(*) as operations,
    COUNT(DISTINCT node_id) as unique_nodes,
    MAX(timestamp) as last_operation
FROM execution;

-- View for anomaly detection rate
CREATE OR REPLACE VIEW anomaly_rate AS
SELECT 
    node_id,
    COUNT(*) as total_analyses,
    SUM(CASE WHEN state != 'NORMAL' THEN 1 ELSE 0 END) as anomalies_detected,
    ROUND(100.0 * SUM(CASE WHEN state != 'NORMAL' THEN 1 ELSE 0 END) / COUNT(*), 2) as anomaly_percentage,
    MAX(timestamp) as last_analysis
FROM "analyze"
GROUP BY node_id;

-- ============================================================================
-- GRANT PERMISSIONS (adjust username as needed)
-- ============================================================================

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Show all created tables
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Show table row counts
SELECT 
    'water_quality' as table_name, COUNT(*) as row_count FROM water_quality
UNION ALL
SELECT 'water_level', COUNT(*) FROM water_level
UNION ALL
SELECT 'water_flow', COUNT(*) FROM water_flow
UNION ALL
SELECT 'motor', COUNT(*) FROM motor
UNION ALL
SELECT 'thresholds', COUNT(*) FROM thresholds
UNION ALL
SELECT 'plans', COUNT(*) FROM plans
UNION ALL
SELECT 'nodes', COUNT(*) FROM nodes
UNION ALL
SELECT 'analyze', COUNT(*) FROM "analyze"
UNION ALL
SELECT 'plan_selection', COUNT(*) FROM plan_selection
UNION ALL
SELECT 'execution', COUNT(*) FROM execution
UNION ALL
SELECT 'execution_log', COUNT(*) FROM execution_log;

COMMIT;

-- Success message
SELECT '✅ Database setup complete! All tables created successfully.' as status;
