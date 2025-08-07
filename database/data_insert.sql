-- Sample data for motor_sensor table
INSERT INTO motor_sensor (node_id, status, voltage, current, power, energy, frequency, power_factor, timestamp)
VALUES ('motor_1', 'ON', 230.0, 5.0, 1150.0, 10.0, 50.0, 0.95, NOW());

-- Sample data for water_flow_sensor table
INSERT INTO water_flow_sensor (node_id, flowrate, total_flow, pressure, pressure_voltage, timestamp)
VALUES ('water_flow_1', 3.5, 100.0, 1.2, 1.0, NOW());

-- Sample data for water_level_sensor table
INSERT INTO water_level_sensor (node_id, water_level, temperature, timestamp)
VALUES ('water_level_1', 5.0, 25.0, NOW());

-- Sample data for water_quality_sensor table
INSERT INTO water_quality_sensor (node_id, temperature, tds_voltage, uncompensated_tds, compensated_tds, timestamp)
VALUES ('water_quality_1', 28.0, 0.9, 200.0, 400.0, NOW());

-- Sample thresholds for each sensor type
INSERT INTO thresholds (node_id, sensor_type, parameter, min_value, max_value)
VALUES
  ('motor_1', 'motor_sensor', 'voltage', 220.0, 240.0),
  ('motor_1', 'motor_sensor', 'current', 3.0, 10.0),
  ('motor_1', 'motor_sensor', 'power_factor', 0.8, 1.0),
  ('water_flow_1', 'water_flow_sensor', 'flowrate', 1.0, 10.0),
  ('water_flow_1', 'water_flow_sensor', 'pressure', 1.0, 5.0),
  ('water_level_1', 'water_level_sensor', 'water_level', 2.0, 8.0),
  ('water_quality_1', 'water_quality_sensor', 'compensated_tds', 100.0, 500.0),
  ('water_quality_1', 'water_quality_sensor', 'temperature', 10.0, 35.0);
