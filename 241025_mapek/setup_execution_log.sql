-- Database setup for IoT Gateway execution logging
-- Run this after setting up the main MAPE-K database

-- Create execution log table to track all commands sent to devices
CREATE TABLE IF NOT EXISTS execution_log (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    plan_code VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL,  -- 'success' or 'failed'
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_execution_log_node_id ON execution_log(node_id);
CREATE INDEX IF NOT EXISTS idx_execution_log_timestamp ON execution_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_execution_log_status ON execution_log(status);

-- View to see recent executions
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

-- View to see execution statistics
CREATE OR REPLACE VIEW execution_stats AS
SELECT 
    node_id,
    COUNT(*) as total_executions,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
    MAX(timestamp) as last_execution
FROM execution_log
GROUP BY node_id;

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON execution_log TO postgres;
-- GRANT ALL PRIVILEGES ON recent_executions TO postgres;
-- GRANT ALL PRIVILEGES ON execution_stats TO postgres;

COMMIT;

-- Verify tables created
SELECT 'Execution log table created successfully' as message;
SELECT * FROM execution_stats;
