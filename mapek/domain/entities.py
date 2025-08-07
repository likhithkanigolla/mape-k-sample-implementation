from mapek.domain.models import SensorReading
from typing import List, Dict
from datetime import datetime
import numpy as np

class DataQualityReport:
    def __init__(self, reading_id: str, quality_score: float, issues: List[str]):
        self.reading_id = reading_id
        self.quality_score = quality_score
        self.issues = issues

class DataQualityChecker:
    def __init__(self, historical_data: Dict[str, List[SensorReading]] = None):
        self.historical_data = historical_data or {}

    def is_outlier(self, value, param: str, node_id: str) -> bool:
        # Simple 3-sigma rule
        if node_id in self.historical_data and param in ['water_level', 'temperature', 'tds_voltage', 'flow_rate']:
            vals = [getattr(r, param) for r in self.historical_data[node_id] if getattr(r, param) is not None]
            if len(vals) > 10:
                mean = np.mean(vals)
                std = np.std(vals)
                if abs(value - mean) > 3 * std:
                    return True
        return False

    def check_quality(self, reading: SensorReading) -> DataQualityReport:
        issues = []
        # Outlier check
        for param in ['water_level', 'temperature', 'tds_voltage', 'flow_rate']:
            value = getattr(reading, param)
            if value is not None and self.is_outlier(value, param, reading.node_id):
                issues.append(f'{param}_outlier')
        # Freshness check
        if (datetime.now() - reading.timestamp).seconds > 300:
            issues.append('stale_data')
        # Add more checks as needed
        quality_score = 1.0 - 0.2 * len(issues)
        return DataQualityReport(reading_id=reading.node_id, quality_score=quality_score, issues=issues)
