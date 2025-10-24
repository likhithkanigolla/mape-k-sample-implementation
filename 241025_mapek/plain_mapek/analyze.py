"""
Analyze component - Analyzes sensor data against thresholds
Simple implementation without design patterns
"""
from logger import logger
from knowledge import get_db_conn

class Analyzer:
    """Analyzer service to check sensor data against thresholds"""
    
    def __init__(self):
        self.thresholds = self._load_thresholds()
        logger.info("Analyzer service initialized")
    
    def _load_thresholds(self):
        """Load thresholds from database"""
        thresholds = {}
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            cur.execute("SELECT parameter, min_value, max_value FROM thresholds")
            rows = cur.fetchall()
            
            for row in rows:
                parameter = row[0]
                min_val = row[1]
                max_val = row[2]
                thresholds[parameter] = {'min': min_val, 'max': max_val}
            
            cur.close()
            conn.close()
            
            logger.info(f"Loaded {len(thresholds)} thresholds")
            
        except Exception as e:
            logger.error(f"Error loading thresholds: {e}")
        
        return thresholds
    
    def analyze(self, sensor_data_list):
        """Analyze sensor data against thresholds"""
        analysis_results = []
        
        for sensor_data in sensor_data_list:
            node_id = sensor_data.get('node_id')
            result = {'node_id': node_id}
            violations = 0
            total_params = 0
            
            # Check each parameter against thresholds
            for param, value in sensor_data.items():
                if param in ['node_id', 'timestamp']:
                    continue
                
                if value is None:
                    result[param] = 0  # Missing data is a violation
                    violations += 1
                    total_params += 1
                    continue
                
                # Check if threshold exists for this parameter
                if param in self.thresholds:
                    threshold = self.thresholds[param]
                    min_val = threshold['min']
                    max_val = threshold['max']
                    
                    if min_val <= value <= max_val:
                        result[param] = 1  # Within threshold (good)
                    else:
                        result[param] = 0  # Outside threshold (bad)
                        violations += 1
                    
                    total_params += 1
                else:
                    # No threshold defined, assume good
                    result[param] = 1
                    total_params += 1
            
            # Determine overall state
            if total_params == 0:
                result['state'] = 'unknown'
            elif violations == 0:
                result['state'] = 'normal'
            elif violations < total_params / 2:
                result['state'] = 'warning'
            else:
                result['state'] = 'critical'
            
            result['violations'] = violations
            result['total_params'] = total_params
            
            analysis_results.append(result)
            
            logger.info(f"Analyzer: {node_id} - State: {result['state']} ({violations}/{total_params} violations)")
        
        return analysis_results
