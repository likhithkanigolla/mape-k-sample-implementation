"""
Monitor component - Reads sensor data from database
Includes verification of plan effectiveness using knowledge base
"""
import psycopg2
from datetime import datetime
from logger import logger
from knowledge import get_db_conn, get_node_ids, KnowledgeBase

class Monitor:
    """Monitor service to read sensor data and verify plan effectiveness"""
    
    def __init__(self):
        self.kb = KnowledgeBase()
        self.stale_after_seconds = 180
        logger.info("Monitor service initialized")

    def _with_monitor_metadata(self, node_id, sensor_data):
        """Attach monitor metadata used by scenario detection in Analyzer."""
        timestamp = sensor_data.get('timestamp')
        monitor_meta = {
            'is_data_missing': timestamp is None,
            'data_age_seconds': None,
            'is_stale': True,
            'stale_after_seconds': self.stale_after_seconds,
        }

        if timestamp is not None:
            age_seconds = max(0.0, (datetime.now() - timestamp).total_seconds())
            monitor_meta['data_age_seconds'] = age_seconds
            monitor_meta['is_stale'] = age_seconds > self.stale_after_seconds

        sensor_data['_monitor'] = monitor_meta
        if monitor_meta['is_data_missing']:
            logger.warning(f"Monitor: No data found for {node_id}")
        elif monitor_meta['is_stale']:
            logger.warning(
                f"Monitor: Stale data for {node_id} "
                f"({monitor_meta['data_age_seconds']:.0f}s old)"
            )

        return sensor_data
    
    def read_sensors(self):
        """Read sensor data from database for all nodes"""
        sensor_data_list = []
        node_ids = get_node_ids()
        
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            for node_id in node_ids:
                sensor_data = {'node_id': node_id}
                row_found = False
                
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
                        row_found = True
                        sensor_data['timestamp'] = row[0]
                        sensor_data['temperature'] = row[1]
                        sensor_data['tds_voltage'] = row[2]
                        sensor_data['uncompensated_tds'] = row[3]
                        sensor_data['compensated_tds'] = row[4]
                        sensor_data_list.append(self._with_monitor_metadata(node_id, sensor_data))
                
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
                        row_found = True
                        sensor_data['timestamp'] = row[0]
                        sensor_data['flowrate'] = row[1]
                        sensor_data['total_flow'] = row[2]
                        sensor_data['pressure'] = row[3]
                        sensor_data['pressure_voltage'] = row[4]
                        sensor_data_list.append(self._with_monitor_metadata(node_id, sensor_data))
                
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
                        row_found = True
                        sensor_data['timestamp'] = row[0]
                        sensor_data['water_level'] = row[1]
                        sensor_data['temperature'] = row[2]
                        sensor_data_list.append(self._with_monitor_metadata(node_id, sensor_data))
                
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
                        row_found = True
                        sensor_data['timestamp'] = row[0]
                        sensor_data['status'] = row[1]
                        sensor_data['voltage'] = row[2]
                        sensor_data['current'] = row[3]
                        sensor_data['power'] = row[4]
                        sensor_data['energy'] = row[5]
                        sensor_data['frequency'] = row[6]
                        sensor_data['power_factor'] = row[7]
                        sensor_data_list.append(self._with_monitor_metadata(node_id, sensor_data))

                if not row_found:
                    # Keep placeholder entries so analyzer can trigger missing-data scenarios.
                    sensor_data_list.append(self._with_monitor_metadata(node_id, sensor_data))
            
            cur.close()
            conn.close()
            
            logger.info(f"Monitor: Read data from {len(sensor_data_list)} sensors")
            
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        
        return sensor_data_list
