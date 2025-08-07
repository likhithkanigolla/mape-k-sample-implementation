-- Plans for MAPE-K system
-- Generic plans for MAPE-K system
INSERT INTO plan (plan_id, node_id, command, parameters, priority, description)
VALUES
  ('WL001', 'motor_1', 'turn_on_motor', '{"condition": "water_level_low"}', 1, 'Motor Start when OHT below minimum'),
  ('WL002', 'motor_1', 'turn_off_motor', '{"condition": "water_level_high"}', 1, 'Motor Stop when OHT full'),
  ('WL003', 'motor_1', 'emergency_stop', '{"condition": "safety_threshold_exceeded"}', 1, 'Emergency Motor Stop and Alarm'),
  ('SH001', 'water_flow_1', 'restart_node', '{"reason": "data_not_posting"}', 2, 'Restart node if data not posting'),
  ('SH002', 'motor_1', 'restart_node', '{"reason": "sensor_anomaly"}', 2, 'Restart node on sensor anomaly'),
  ('SH003', 'water_level_1', 'restart_service', '{"service": "water_level"}', 3, 'Restart water level service'),
  ('CM001', 'water_quality_1', 'calibrate_sensor', '{"sensor": "tds"}', 4, 'Sensor recalibration');
