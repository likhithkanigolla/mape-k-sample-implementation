import pytest
from unittest.mock import Mock
from mapek.application.services.analyzer_service import Analyzer
from mapek.infrastructure.database.repositories import ThresholdRepository

class TestAnalyzer:
    def test_analyze_normal_readings(self):
        threshold_repo = Mock(spec=ThresholdRepository)
        threshold_repo.get_threshold.return_value = (10.0, 50.0)
        analyzer = Analyzer(threshold_repo)
        result = analyzer.analyze([
            {"node_id": "test", "temperature": 25.0, "timestamp": "2025-08-08T12:00:00"}
        ])
        assert result[0]["temperature"] == 1
        assert result[0]["state"] == "normal"

    def test_analyze_threshold_violation(self):
        threshold_repo = Mock(spec=ThresholdRepository)
        threshold_repo.get_threshold.return_value = (10.0, 50.0)
        analyzer = Analyzer(threshold_repo)
        result = analyzer.analyze([
            {"node_id": "test", "temperature": 55.0, "timestamp": "2025-08-08T12:00:00"}
        ])
        assert result[0]["temperature"] == 0
        assert result[0]["state"] != "normal"
