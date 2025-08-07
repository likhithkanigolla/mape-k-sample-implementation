from mapek.domain.models import SensorReading
from mapek.infrastructure.database.repositories import ThresholdRepository
from mapek.domain.entities import DataQualityChecker
from mapek.logger import logger, mape_loop_duration, sensor_readings_total, threshold_violations
from typing import List, Dict
from datetime import datetime
def _noop_decorator(func):
    return func

class Analyzer:
    def __init__(self, threshold_repo: ThresholdRepository):
        self.threshold_repo = threshold_repo
        self.quality_checker = DataQualityChecker()

    def analyze(self, sensor_data: List[Dict]) -> List[Dict]:
        # If Prometheus is available, wrap with timing; else, no-op
        method = self._analyze_with_timing if mape_loop_duration else self._analyze_no_timing
        return method(sensor_data)

    def _analyze_with_timing(self, sensor_data: List[Dict]) -> List[Dict]:
        @_noop_decorator if mape_loop_duration is None else mape_loop_duration.time()
        def inner(sensor_data):
            return self._analyze_no_timing(sensor_data)
        return inner(sensor_data)

    def _analyze_no_timing(self, sensor_data: List[Dict]) -> List[Dict]:
        results = []
        for data in sensor_data:
            try:
                reading = SensorReading(**data)
                quality_report = self.quality_checker.check_quality(reading)
                node_result = {'node_id': reading.node_id}
                bad_count = 0
                quality_score = quality_report.quality_score
                # Only check fields present in the data
                for key in data:
                    if key in ['node_id', 'timestamp']:
                        continue
                    value = data[key]
                    if sensor_readings_total:
                        sensor_readings_total.labels(node_id=reading.node_id, sensor_type=key).inc()
                    if value is None:
                        logger.warning(f"Null value for {key} in node {reading.node_id}")
                        node_result[key] = 0
                        bad_count += 1
                        quality_score -= 0.2
                        continue
                    threshold = self.threshold_repo.get_threshold(key)
                    if threshold:
                        min_val, max_val = threshold
                        status = 1 if (min_val <= value <= max_val) else 0
                        node_result[key] = status
                        if status == 0 and threshold_violations:
                            threshold_violations.labels(node_id=reading.node_id, parameter=key).inc()
                            bad_count += 1
                    else:
                        node_result[key] = 1
                node_result['state'] = (
                    'normal' if quality_score > 0.8 else
                    'alert' if bad_count == 1 or quality_score > 0.5 else
                    'emergency'
                )
                results.append(node_result)
            except Exception as e:
                logger.error(f"Analyzer error for node {data.get('node_id')}: {e}")
                continue
        return results
