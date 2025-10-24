"""
Monitor component - Reads sensor data from database
Simple implementation without design patterns
"""
import psycopg2
from logger import logger
from knowledge import get_db_conn, get_node_ids

class Monitor:
    """Monitor service to read sensor data"""
    
    def __init__(self):
        logger.info("Monitor service initialized")
    
    def read_sensors(self):
        """Read sensor data from database for all nodes"""
        sensor_data_list = []
        node_ids = get_node_ids()
        
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            for node_id in node_ids:
                sensor_data = {'node_id': node_id}
                
                # Read water quality sensor data
                if "water_quality" in node_id:
                    cur.execute("""
                        SELECT timestamp, temperature, tds_voltage, 
                               uncompensated_tds, compensated_tds 
                        FROM water_quality 
                        WHERE node_id = %s 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """, (node_id,))
                    row = cur.fetchone()
                    
                    if row:
                        sensor_data['timestamp'] = row[0]
                        sensor_data['temperature'] = row[1]
                        sensor_data['tds_voltage'] = row[2]
                        sensor_data['uncompensated_tds'] = row[3]
                        sensor_data['compensated_tds'] = row[4]
                        sensor_data_list.append(sensor_data)
                
                # Read water flow sensor data
                elif "water_flow" in node_id:
                    cur.execute("""
                        SELECT timestamp, flowrate, total_flow, 
                               pressure, pressure_voltage 
                        FROM water_flow 
                        WHERE node_id = %s 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """, (node_id,))
                    row = cur.fetchone()
                    
                    if row:
                        sensor_data['timestamp'] = row[0]
                        sensor_data['flowrate'] = row[1]
                        sensor_data['total_flow'] = row[2]
                        sensor_data['pressure'] = row[3]
                        sensor_data['pressure_voltage'] = row[4]
                        sensor_data_list.append(sensor_data)
                
                # Read water level sensor data
                elif "water_level" in node_id:
                    cur.execute("""
                        SELECT timestamp, water_level, temperature 
                        FROM water_level 
                        WHERE node_id = %s 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """, (node_id,))
                    row = cur.fetchone()
                    
                    if row:
                        sensor_data['timestamp'] = row[0]
                        sensor_data['water_level'] = row[1]
                        sensor_data['temperature'] = row[2]
                        sensor_data_list.append(sensor_data)
                
                # Read motor sensor data
                elif "motor" in node_id:
                    cur.execute("""
                        SELECT timestamp, status, voltage, current, 
                               power, energy, frequency, power_factor 
                        FROM motor 
                        WHERE node_id = %s 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """, (node_id,))
                    row = cur.fetchone()
                    
                    if row:
                        sensor_data['timestamp'] = row[0]
                        sensor_data['status'] = row[1]
                        sensor_data['voltage'] = row[2]
                        sensor_data['current'] = row[3]
                        sensor_data['power'] = row[4]
                        sensor_data['energy'] = row[5]
                        sensor_data['frequency'] = row[6]
                        sensor_data['power_factor'] = row[7]
                        sensor_data_list.append(sensor_data)
            
            cur.close()
            conn.close()
            
            logger.info(f"Monitor: Read data from {len(sensor_data_list)} sensors")
            
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        
        return sensor_data_list
