INSERT INTO plan (plan_code, node_id, command, parameters, priority, state, description)
VALUES
  ('WL001', 'motor_1', 'turn_on_motor', '{"condition": "water_level_low"}', 1, 'alert', 'Motor Start when OHT below minimum'),
  ('WL002', 'motor_1', 'turn_off_motor', '{"condition": "water_level_high"}', 1, 'alert', 'Motor Stop when OHT full'),
  ('WL003', 'motor_1', 'emergency_stop', '{"condition": "safety_threshold_exceeded"}', 1, 'emergency', 'Emergency Motor Stop and Alarm'),
  ('SH001', 'water_flow_1', 'restart_node', '{"reason": "data_not_posting"}', 2, 'data_not_posting', 'Restart node if data not posting'),
  ('SH002', 'motor_1', 'restart_node', '{"reason": "sensor_anomaly"}', 2, 'alert', 'Restart node on sensor anomaly'),
  ('SH003', 'water_level_1', 'restart_service', '{"service": "water_level"}', 3, 'service_restart', 'Restart water level service'),
  ('CM001', 'water_quality_1', 'calibrate_sensor', '{"sensor": "tds"}', 4, 'calibration', 'Sensor recalibration');