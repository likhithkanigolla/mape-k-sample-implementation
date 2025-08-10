from mapek.infrastructure.database.repositories import NodeRepository
from mapek.logger import logger
from typing import List, Dict

class Monitor:
    def __init__(self, node_repo: NodeRepository):
        self.node_repo = node_repo

    def read_sensors(self) -> List[Dict]:
        from mapek.config.database import database_transaction
        sensor_data_list = []
        node_ids = self.node_repo.get_node_ids()
        with database_transaction() as conn:
            cur = conn.cursor()
            for node_id in node_ids:
                sensor_data = {"node_id": node_id}
                if "water_quality" in node_id:
                    try:
                        cur.execute("SELECT timestamp, temperature, tds_voltage, uncompensated_tds, compensated_tds FROM water_quality WHERE node_id = %s ORDER BY timestamp DESC LIMIT 1", (node_id,))
                        row = cur.fetchone()
                        logger.info(f"Raw DB row for {node_id} (water_quality): {row}")
                        if row:
                            sensor_data["timestamp"] = row[0]
                            if row[1] is not None: sensor_data["temperature"] = row[1]
                            if row[2] is not None: sensor_data["tds_voltage"] = row[2]
                            if row[3] is not None: sensor_data["uncompensated_tds"] = row[3]
                            if row[4] is not None: sensor_data["compensated_tds"] = row[4]
                            sensor_data_list.append(sensor_data)
                    except Exception as e:
                        logger.error(f"Monitor DB error for {node_id} in water_quality: {e}")
                        continue
                elif "water_flow" in node_id:
                    try:
                        cur.execute("SELECT timestamp, flowrate, total_flow, pressure, pressure_voltage FROM water_flow WHERE node_id = %s ORDER BY timestamp DESC LIMIT 1", (node_id,))
                        row = cur.fetchone()
                        logger.info(f"Raw DB row for {node_id} (water_flow): {row}")
                        if row:
                            sensor_data["timestamp"] = row[0]
                            if row[1] is not None: sensor_data["flowrate"] = row[1]
                            if row[2] is not None: sensor_data["total_flow"] = row[2]
                            if row[3] is not None: sensor_data["pressure"] = row[3]
                            if row[4] is not None: sensor_data["pressure_voltage"] = row[4]
                            sensor_data_list.append(sensor_data)
                    except Exception as e:
                        logger.error(f"Monitor DB error for {node_id} in water_flow: {e}")
                        continue
                elif "water_level" in node_id:
                    try:
                        cur.execute("SELECT timestamp, water_level, temperature FROM water_level WHERE node_id = %s ORDER BY timestamp DESC LIMIT 1", (node_id,))
                        row = cur.fetchone()
                        logger.info(f"Raw DB row for {node_id} (water_level): {row}")
                        if row:
                            sensor_data["timestamp"] = row[0]
                            if row[1] is not None: sensor_data["water_level"] = row[1]
                            if row[2] is not None: sensor_data["temperature"] = row[2]
                            sensor_data_list.append(sensor_data)
                    except Exception as e:
                        logger.error(f"Monitor DB error for {node_id} in water_level: {e}")
                        continue
                elif "motor" in node_id:
                    try:
                        cur.execute("SELECT timestamp, status, voltage, current, power, energy, frequency, power_factor FROM motor WHERE node_id = %s ORDER BY timestamp DESC LIMIT 1", (node_id,))
                        row = cur.fetchone()
                        logger.info(f"Raw DB row for {node_id} (motor): {row}")
                        if row:
                            sensor_data["timestamp"] = row[0]
                            if row[1] is not None: sensor_data["status"] = row[1]
                            if row[2] is not None: sensor_data["voltage"] = row[2]
                            if row[3] is not None: sensor_data["current"] = row[3]
                            if row[4] is not None: sensor_data["power"] = row[4]
                            if row[5] is not None: sensor_data["energy"] = row[5]
                            if row[6] is not None: sensor_data["frequency"] = row[6]
                            if row[7] is not None: sensor_data["power_factor"] = row[7]
                            sensor_data_list.append(sensor_data)
                    except Exception as e:
                        logger.error(f"Monitor DB error for {node_id} in motor: {e}")
                        continue
                else:
                    # Default: just log all columns from water_level
                    try:
                        cur.execute("SELECT * FROM water_level WHERE node_id = %s ORDER BY timestamp DESC LIMIT 1", (node_id,))
                        row = cur.fetchone()
                        logger.info(f"Raw DB row for {node_id} (default/water_level): {row}")
                        if row:
                            for i, val in enumerate(row[1:], start=1):
                                if val is not None:
                                    sensor_data[f"param_{i}"] = val
                            sensor_data_list.append(sensor_data)
                    except Exception as e:
                        logger.error(f"Monitor DB error for {node_id} in default: {e}")
                        continue
        return sensor_data_list if sensor_data_list else []

    # get_raw_data is now obsolete
