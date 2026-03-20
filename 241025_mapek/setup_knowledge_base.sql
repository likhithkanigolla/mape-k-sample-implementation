-- ============================================================================
-- Knowledge Base Tables for Intelligent MAPE-K System
-- ============================================================================

-- Extend the existing plans table with learning capabilities
-- Add columns to track effectiveness and parameter-specific plans
ALTER TABLE plans 
ADD COLUMN IF NOT EXISTS parameter VARCHAR(50),              -- Which parameter this plan addresses (temperature, tds, etc.)
ADD COLUMN IF NOT EXISTS success_rate DECIMAL(5,2) DEFAULT 50.00,  -- Historical success rate (starts at 50%)
ADD COLUMN IF NOT EXISTS total_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS successful_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_used TIMESTAMP,
ADD COLUMN IF NOT EXISTS escalation_level INTEGER DEFAULT 1;  -- 1=restart service, 2=restart device, 3=shutdown

CREATE INDEX IF NOT EXISTS idx_plans_parameter ON plans(parameter);
CREATE INDEX IF NOT EXISTS idx_plans_success ON plans(success_rate);

-- Table to store plan execution history and effectiveness
CREATE TABLE IF NOT EXISTS plan_effectiveness (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    parameter VARCHAR(50),                       -- Which parameter had the issue (temperature, tds_voltage, etc.)
    problem_value DECIMAL(10,2),                 -- The value that triggered the problem
    threshold_min DECIMAL(10,2),                 -- Expected min value
    threshold_max DECIMAL(10,2),                 -- Expected max value
    plan_code VARCHAR(100) NOT NULL,             -- Plan that was executed
    execution_timestamp TIMESTAMP NOT NULL,
    verification_timestamp TIMESTAMP,            -- When we checked if it worked
    was_successful BOOLEAN,                      -- Did it fix the problem?
    cycles_to_fix INTEGER,                       -- How many cycles until fixed
    escalation_level INTEGER DEFAULT 1,          -- Which escalation level was this
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_plan_eff_node ON plan_effectiveness(node_id);
CREATE INDEX IF NOT EXISTS idx_plan_eff_param ON plan_effectiveness(parameter);
CREATE INDEX IF NOT EXISTS idx_plan_eff_plan ON plan_effectiveness(plan_code);
CREATE INDEX IF NOT EXISTS idx_plan_eff_success ON plan_effectiveness(was_successful);

-- Table to track ongoing issues that need resolution (at parameter level)
CREATE TABLE IF NOT EXISTS issue_tracking (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    parameter VARCHAR(50) NOT NULL,              -- Specific parameter with issue (temperature, tds, flow, etc.)
    problem_value DECIMAL(10,2),                 -- Current problematic value
    threshold_min DECIMAL(10,2),                 -- Expected min
    threshold_max DECIMAL(10,2),                 -- Expected max
    detected_timestamp TIMESTAMP NOT NULL,
    plan_executed VARCHAR(100),
    execution_timestamp TIMESTAMP,
    escalation_level INTEGER DEFAULT 1,          -- Current escalation level (1, 2, 3)
    attempts INTEGER DEFAULT 0,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_timestamp TIMESTAMP,
    UNIQUE(node_id, parameter, detected_timestamp)
);

CREATE INDEX IF NOT EXISTS idx_issue_node ON issue_tracking(node_id);
CREATE INDEX IF NOT EXISTS idx_issue_param ON issue_tracking(parameter);
CREATE INDEX IF NOT EXISTS idx_issue_resolved ON issue_tracking(is_resolved);

-- ============================================================================
-- Insert Parameter-Specific Plans with Escalation Levels
-- ============================================================================

-- Temperature Issues (3 escalation levels)
INSERT INTO plans (state, plan_code, description, priority, parameter, escalation_level, success_rate) VALUES
('HIGH_TEMPERATURE', 'RESTART_TEMP_SENSOR', 'Restart temperature sensor service', 1, 'temperature', 1, 80.00),
('HIGH_TEMPERATURE', 'RESTART_DEVICE', 'Restart entire device', 2, 'temperature', 2, 70.00),
('HIGH_TEMPERATURE', 'EMERGENCY_SHUTDOWN', 'Emergency system shutdown', 3, 'temperature', 3, 95.00);

-- TDS/Water Quality Issues
INSERT INTO plans (state, plan_code, description, priority, parameter, escalation_level, success_rate) VALUES
('HIGH_TDS', 'RECALIBRATE_TDS_SENSOR', 'Recalibrate TDS sensor', 1, 'compensated_tds', 1, 85.00),
('HIGH_TDS', 'CLEAN_SENSOR', 'Clean TDS sensor probe', 2, 'compensated_tds', 2, 75.00),
('HIGH_TDS', 'REPLACE_SENSOR', 'Replace TDS sensor', 3, 'compensated_tds', 3, 90.00),

('HIGH_TDS_VOLTAGE', 'RECALIBRATE_TDS_VOLTAGE', 'Recalibrate TDS voltage sensor', 1, 'tds_voltage', 1, 80.00),
('HIGH_TDS_VOLTAGE', 'CHECK_POWER_SUPPLY', 'Check power supply voltage', 2, 'tds_voltage', 2, 70.00),
('HIGH_TDS_VOLTAGE', 'RESTART_DEVICE', 'Restart device', 3, 'tds_voltage', 3, 85.00);

-- Water Level Issues (use ON CONFLICT to avoid duplicates)
INSERT INTO plans (state, plan_code, description, priority, parameter, escalation_level, success_rate) VALUES
('LOW_WATER_LEVEL', 'ACTIVATE_INLET_VALVE', 'Activate inlet valve', 1, 'water_level', 1, 90.00),
('LOW_WATER_LEVEL', 'ACTIVATE_PUMP', 'Activate water pump', 2, 'water_level', 2, 85.00),
('LOW_WATER_LEVEL', 'CHECK_INLET_BLOCKAGE', 'Check for inlet blockage', 3, 'water_level', 3, 75.00),

('HIGH_WATER_LEVEL', 'STOP_INLET', 'Stop water inlet', 1, 'water_level', 1, 95.00),
('HIGH_WATER_LEVEL', 'ACTIVATE_DRAIN', 'Activate drain valve', 2, 'water_level', 2, 90.00),
('HIGH_WATER_LEVEL', 'EMERGENCY_STOP', 'Emergency stop all pumps', 3, 'water_level', 3, 100.00)
ON CONFLICT (state, plan_code) DO UPDATE SET
    parameter = EXCLUDED.parameter,
    escalation_level = EXCLUDED.escalation_level,
    success_rate = EXCLUDED.success_rate;

-- Flow Rate Issues
INSERT INTO plans (state, plan_code, description, priority, parameter, escalation_level, success_rate) VALUES
('HIGH_FLOW_RATE', 'REDUCE_VALVE_OPENING', 'Reduce valve opening by 20%', 1, 'flowrate', 1, 85.00),
('HIGH_FLOW_RATE', 'REDUCE_PUMP_SPEED', 'Reduce pump speed', 2, 'flowrate', 2, 80.00),
('HIGH_FLOW_RATE', 'STOP_PUMP', 'Stop pump', 3, 'flowrate', 3, 95.00),

('LOW_FLOW_RATE', 'INCREASE_VALVE_OPENING', 'Increase valve opening by 20%', 1, 'flowrate', 1, 85.00),
('LOW_FLOW_RATE', 'INCREASE_PUMP_SPEED', 'Increase pump speed', 2, 'flowrate', 2, 75.00),
('LOW_FLOW_RATE', 'CHECK_BLOCKAGES', 'Check for pipe blockages', 3, 'flowrate', 3, 70.00)
ON CONFLICT (state, plan_code) DO UPDATE SET
    parameter = EXCLUDED.parameter,
    escalation_level = EXCLUDED.escalation_level,
    success_rate = EXCLUDED.success_rate;

-- Pressure Issues
INSERT INTO plans (state, plan_code, description, priority, parameter, escalation_level, success_rate) VALUES
('HIGH_PRESSURE', 'REDUCE_PUMP_SPEED', 'Reduce pump speed gradually', 1, 'pressure', 1, 80.00),
('HIGH_PRESSURE', 'OPEN_PRESSURE_RELIEF', 'Open pressure relief valve', 2, 'pressure', 2, 90.00),
('HIGH_PRESSURE', 'EMERGENCY_SHUTDOWN', 'Emergency shutdown', 3, 'pressure', 3, 95.00)
ON CONFLICT (state, plan_code) DO UPDATE SET
    parameter = EXCLUDED.parameter,
    escalation_level = EXCLUDED.escalation_level,
    success_rate = EXCLUDED.success_rate;

-- Motor/Power Issues
INSERT INTO plans (state, plan_code, description, priority, parameter, escalation_level, success_rate) VALUES
('HIGH_CURRENT', 'REDUCE_MOTOR_LOAD', 'Reduce motor load by 30%', 1, 'current', 1, 75.00),
('HIGH_CURRENT', 'CHECK_MOTOR_BEARINGS', 'Check motor bearings', 2, 'current', 2, 70.00),
('HIGH_CURRENT', 'STOP_MOTOR', 'Stop motor to prevent damage', 3, 'current', 3, 90.00),

('LOW_VOLTAGE', 'SWITCH_TO_BACKUP_POWER', 'Switch to backup power source', 1, 'voltage', 1, 85.00),
('LOW_VOLTAGE', 'CHECK_POWER_CONNECTION', 'Check power connections', 2, 'voltage', 2, 70.00),
('LOW_VOLTAGE', 'REDUCE_LOAD', 'Reduce system load', 3, 'voltage', 3, 80.00),

('LOW_FREQUENCY', 'CHECK_GRID_CONNECTION', 'Check grid connection', 1, 'frequency', 1, 75.00),
('LOW_FREQUENCY', 'SWITCH_TO_UPS', 'Switch to UPS', 2, 'frequency', 2, 90.00),
('LOW_FREQUENCY', 'GRACEFUL_SHUTDOWN', 'Graceful system shutdown', 3, 'frequency', 3, 95.00),

('LOW_POWER_FACTOR', 'ADD_CAPACITOR_BANK', 'Add capacitor bank', 1, 'power_factor', 1, 85.00),
('LOW_POWER_FACTOR', 'BALANCE_LOAD', 'Balance three-phase load', 2, 'power_factor', 2, 75.00),
('LOW_POWER_FACTOR', 'REDUCE_INDUCTIVE_LOAD', 'Reduce inductive load', 3, 'power_factor', 3, 70.00)
ON CONFLICT (state, plan_code) DO UPDATE SET
    parameter = EXCLUDED.parameter,
    escalation_level = EXCLUDED.escalation_level,
    success_rate = EXCLUDED.success_rate;

-- Default/Fallback Plans
INSERT INTO plans (state, plan_code, description, priority, parameter, escalation_level, success_rate) VALUES
('NORMAL', 'NO_ACTION', 'System operating normally', 1, NULL, 1, 100.00),
('CRITICAL', 'EMERGENCY_SHUTDOWN', 'Emergency system shutdown', 1, NULL, 3, 95.00),
('WARNING', 'INCREASE_MONITORING', 'Increase monitoring frequency', 1, NULL, 1, 80.00),
('ANOMALY', 'RECALIBRATE_ALL', 'Recalibrate all sensors', 1, NULL, 2, 75.00)
ON CONFLICT (state, plan_code) DO UPDATE SET
    parameter = EXCLUDED.parameter,
    escalation_level = EXCLUDED.escalation_level,
    success_rate = EXCLUDED.success_rate;

-- ============================================================================
-- Views for Knowledge Base Analytics
-- ============================================================================

-- View: Best performing plans for each parameter
CREATE OR REPLACE VIEW best_plans_by_parameter AS
SELECT 
    parameter,
    state,
    plan_code,
    success_rate,
    total_attempts,
    successful_attempts,
    escalation_level,
    description
FROM plans
WHERE total_attempts > 0 AND parameter IS NOT NULL
ORDER BY parameter, success_rate DESC, escalation_level ASC;

-- View: Current unresolved issues (parameter-specific)
CREATE OR REPLACE VIEW active_issues AS
SELECT 
    node_id,
    parameter,
    problem_value,
    threshold_min,
    threshold_max,
    detected_timestamp,
    plan_executed,
    execution_timestamp,
    escalation_level,
    attempts,
    EXTRACT(EPOCH FROM (NOW() - detected_timestamp))/60 as minutes_since_detection
FROM issue_tracking
WHERE is_resolved = FALSE
ORDER BY detected_timestamp DESC;

-- View: Plan effectiveness summary by parameter
CREATE OR REPLACE VIEW plan_effectiveness_by_parameter AS
SELECT 
    parameter,
    plan_code,
    COUNT(*) as total_executions,
    SUM(CASE WHEN was_successful THEN 1 ELSE 0 END) as successful_executions,
    ROUND(100.0 * SUM(CASE WHEN was_successful THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate,
    AVG(cycles_to_fix) as avg_cycles_to_fix,
    AVG(escalation_level) as avg_escalation_level,
    MAX(execution_timestamp) as last_used
FROM plan_effectiveness
WHERE was_successful IS NOT NULL
GROUP BY parameter, plan_code
ORDER BY parameter, success_rate DESC;

-- View: Escalation analysis - How often do we need to escalate?
CREATE OR REPLACE VIEW escalation_analysis AS
SELECT 
    node_id,
    parameter,
    COUNT(*) as total_issues,
    AVG(escalation_level) as avg_escalation_level,
    MAX(escalation_level) as max_escalation_reached,
    ROUND(AVG(cycles_to_fix), 2) as avg_cycles_to_fix,
    COUNT(CASE WHEN escalation_level = 1 THEN 1 END) as fixed_at_level_1,
    COUNT(CASE WHEN escalation_level = 2 THEN 1 END) as fixed_at_level_2,
    COUNT(CASE WHEN escalation_level = 3 THEN 1 END) as fixed_at_level_3
FROM plan_effectiveness
WHERE was_successful = TRUE
GROUP BY node_id, parameter
ORDER BY avg_escalation_level DESC;

COMMIT;

SELECT '✅ Knowledge Base tables created successfully!' as status;
SELECT '📊 Parameter-specific plans with escalation levels configured!' as info;
