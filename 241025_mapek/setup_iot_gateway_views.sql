-- ============================================================================
-- IoT Gateway Analytics Views
-- ============================================================================
-- This file creates views for monitoring IoT gateway operations and sensor health

-- View: Sensor health overview
CREATE OR REPLACE VIEW sensor_health AS
SELECT 
    n.node_id,
    n.node_type,
    n.description,
    CASE 
        WHEN wq.timestamp IS NOT NULL THEN 'water_quality'
        WHEN wl.timestamp IS NOT NULL THEN 'water_level'
        WHEN wf.timestamp IS NOT NULL THEN 'water_flow'
        WHEN m.timestamp IS NOT NULL THEN 'motor'
        ELSE 'unknown'
    END as active_sensor_type,
    COALESCE(wq.timestamp, wl.timestamp, wf.timestamp, m.timestamp) as last_reading_time,
    EXTRACT(EPOCH FROM (NOW() - COALESCE(wq.timestamp, wl.timestamp, wf.timestamp, m.timestamp))) as seconds_since_last_reading,
    CASE 
        WHEN EXTRACT(EPOCH FROM (NOW() - COALESCE(wq.timestamp, wl.timestamp, wf.timestamp, m.timestamp))) < 60 THEN 'Healthy'
        WHEN EXTRACT(EPOCH FROM (NOW() - COALESCE(wq.timestamp, wl.timestamp, wf.timestamp, m.timestamp))) < 300 THEN 'Warning'
        ELSE 'Offline'
    END as health_status
FROM nodes n
LEFT JOIN LATERAL (
    SELECT timestamp FROM water_quality WHERE node_id = n.node_id ORDER BY timestamp DESC LIMIT 1
) wq ON TRUE
LEFT JOIN LATERAL (
    SELECT timestamp FROM water_level WHERE node_id = n.node_id ORDER BY timestamp DESC LIMIT 1
) wl ON TRUE
LEFT JOIN LATERAL (
    SELECT timestamp FROM water_flow WHERE node_id = n.node_id ORDER BY timestamp DESC LIMIT 1
) wf ON TRUE
LEFT JOIN LATERAL (
    SELECT timestamp FROM motor WHERE node_id = n.node_id ORDER BY timestamp DESC LIMIT 1
) m ON TRUE;

-- View: Recent gateway activity
CREATE OR REPLACE VIEW recent_gateway_activity AS
SELECT 
    'water_quality' as sensor_type,
    node_id,
    timestamp,
    temperature,
    tds_voltage,
    compensated_tds
FROM water_quality
WHERE timestamp > NOW() - INTERVAL '1 hour'

UNION ALL

SELECT 
    'water_level' as sensor_type,
    node_id,
    timestamp,
    water_level,
    NULL as tds_voltage,
    NULL as compensated_tds
FROM water_level
WHERE timestamp > NOW() - INTERVAL '1 hour'

UNION ALL

SELECT 
    'water_flow' as sensor_type,
    node_id,
    timestamp,
    flowrate,
    pressure,
    NULL as compensated_tds
FROM water_flow
WHERE timestamp > NOW() - INTERVAL '1 hour'

UNION ALL

SELECT 
    'motor' as sensor_type,
    node_id,
    timestamp,
    current,
    voltage,
    frequency
FROM motor
WHERE timestamp > NOW() - INTERVAL '1 hour'

ORDER BY timestamp DESC;

-- View: Command execution summary
CREATE OR REPLACE VIEW command_execution_summary AS
SELECT 
    e.node_id,
    e.plan_code,
    p.description,
    COUNT(*) as execution_count,
    COUNT(CASE WHEN el.status = 'success' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN el.status = 'failed' THEN 1 END) as failed_executions,
    ROUND(100.0 * COUNT(CASE WHEN el.status = 'success' THEN 1 END) / COUNT(*), 2) as success_rate_pct,
    MAX(e.timestamp) as last_executed,
    MIN(e.timestamp) as first_executed
FROM execution e
LEFT JOIN plans p ON e.plan_code = p.plan_code
LEFT JOIN execution_log el ON e.node_id = el.node_id AND e.plan_code = el.plan_code
GROUP BY e.node_id, e.plan_code, p.description
ORDER BY execution_count DESC;

-- View: Gateway throughput metrics
CREATE OR REPLACE VIEW gateway_throughput AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as total_sensor_readings,
    COUNT(DISTINCT node_id) as active_nodes,
    ROUND(COUNT(*)::numeric / EXTRACT(EPOCH FROM INTERVAL '1 hour') * 60, 2) as readings_per_minute
FROM (
    SELECT node_id, timestamp FROM water_quality
    UNION ALL
    SELECT node_id, timestamp FROM water_level
    UNION ALL
    SELECT node_id, timestamp FROM water_flow
    UNION ALL
    SELECT node_id, timestamp FROM motor
) all_readings
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

COMMIT;

SELECT '✅ IoT Gateway views created successfully!' as status;
SELECT '📊 Views: sensor_health, recent_gateway_activity, command_execution_summary, gateway_throughput' as info;
