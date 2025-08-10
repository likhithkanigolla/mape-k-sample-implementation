from mapek.domain.models import SensorReading
from mapek.infrastructure.database.repositories import ThresholdRepository
from mapek.domain.entities import DataQualityChecker
from mapek.logger import logger
from typing import List, Dict

class Analyzer:
    def __init__(self, threshold_repo: ThresholdRepository):
        self.threshold_repo = threshold_repo
        self.quality_checker = DataQualityChecker()

    def analyze(self, sensor_data: List[Dict]) -> List[Dict]:
        return self._analyze_data(sensor_data)

    def _analyze_data(self, sensor_data: List[Dict]) -> List[Dict]:
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
                        if status == 0:
                            bad_count += 1
                            quality_score -= 0.15  # Reduce quality score for each threshold violation
                    else:
                        node_result[key] = 1
                
                # Ensure quality score doesn't go below 0
                quality_score = max(0.0, quality_score)
                
                # Fix state determination logic - prioritize bad_count over quality_score
                if bad_count >= 3:
                    state = 'emergency'
                elif bad_count >= 1:
                    state = 'alert'
                elif quality_score > 0.8:
                    state = 'normal'
                else:
                    state = 'alert'
                
                node_result['state'] = state
                logger.info(f"Node {reading.node_id}: bad_count={bad_count}, quality_score={quality_score:.2f}, state={state}")
                results.append(node_result)
            except Exception as e:
                logger.error(f"Analyzer error for node {data.get('node_id')}: {e}")
                continue
        return results
