"""
Property-based testing for MAPE-K system using Hypothesis.
Tests system behavior across a wide range of input conditions.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, Bundle
from typing import List, Dict, Any
from unittest.mock import AsyncMock

from domain.models import SensorData, SystemState
from domain.entities import SystemHealthStatus, ThresholdViolationType
from application.services.analyzer_service import AnalyzerService


# Strategies for generating test data
sensor_types = st.sampled_from(["flow", "pressure", "quality", "temperature"])
sensor_ids = st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
sensor_values = st.floats(min_value=-100.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
timestamps = st.datetimes(min_value=None, max_value=None).map(lambda dt: dt.isoformat() + "Z")


@st.composite
def sensor_data_strategy(draw):
    """Generate valid SensorData instances."""
    return SensorData(
        sensor_id=draw(sensor_ids),
        value=draw(sensor_values),
        timestamp=draw(timestamps),
        sensor_type=draw(sensor_types)
    )


class TestAnalyzerPropertyBased:
    """Property-based tests for the analyzer service."""

    @given(sensor_data_list=st.lists(sensor_data_strategy(), min_size=1, max_size=10))
    @settings(max_examples=50, deadline=None)
    def test_analyzer_always_returns_valid_state(self, sensor_data_list):
        """Test that analyzer always returns a valid system state."""
        # Arrange
        analyzer = AnalyzerService()
        
        # Act
        result = analyzer.analyze(sensor_data_list)
        
        # Assert
        assert isinstance(result, dict)
        assert "state" in result
        assert result["state"] in [SystemState.NORMAL, SystemState.WARNING, SystemState.CRITICAL, SystemState.UNKNOWN]
        assert "quality_score" in result
        assert isinstance(result["quality_score"], (int, float))
        assert 0.0 <= result["quality_score"] <= 1.0

    @given(
        flow_value=st.floats(min_value=0.0, max_value=200.0, allow_nan=False),
        pressure_value=st.floats(min_value=0.0, max_value=10.0, allow_nan=False),
        quality_value=st.floats(min_value=0.0, max_value=10.0, allow_nan=False)
    )
    @settings(max_examples=100)
    def test_quality_score_monotonicity(self, flow_value, pressure_value, quality_value):
        """Test that quality score decreases with threshold violations."""
        # Arrange
        analyzer = AnalyzerService()
        sensor_data = [
            SensorData(sensor_id="flow_01", value=flow_value, timestamp="2024-01-01T10:00:00Z", sensor_type="flow"),
            SensorData(sensor_id="pressure_01", value=pressure_value, timestamp="2024-01-01T10:00:00Z", sensor_type="pressure"),
            SensorData(sensor_id="quality_01", value=quality_value, timestamp="2024-01-01T10:00:00Z", sensor_type="quality")
        ]
        
        # Act
        result = analyzer.analyze(sensor_data)
        
        # Assert
        violation_count = len(result.get("violations", []))
        expected_quality_reduction = violation_count * 0.15
        expected_quality_score = max(0.0, 1.0 - expected_quality_reduction)
        
        # Allow for small floating point differences
        assert abs(result["quality_score"] - expected_quality_score) < 0.001

    @given(sensor_value=st.floats(allow_nan=True, allow_infinity=True))
    def test_analyzer_handles_invalid_sensor_values(self, sensor_value):
        """Test that analyzer gracefully handles invalid sensor values."""
        # Arrange
        analyzer = AnalyzerService()
        
        try:
            sensor_data = [SensorData(
                sensor_id="test_sensor",
                value=sensor_value,
                timestamp="2024-01-01T10:00:00Z",
                sensor_type="flow"
            )]
            
            # Act
            result = analyzer.analyze(sensor_data)
            
            # Assert - should handle gracefully
            if result is not None:
                assert isinstance(result, dict)
                assert "state" in result
        except (ValueError, TypeError):
            # It's acceptable to raise these for truly invalid inputs
            pass


class MapeKStateMachine(RuleBasedStateMachine):
    """Stateful testing for MAPE-K system behavior."""
    
    sensor_data = Bundle('sensor_data')
    analysis_results = Bundle('analysis_results')
    
    def __init__(self):
        super().__init__()
        self.system_state = SystemState.NORMAL
        self.quality_score = 1.0
        self.violation_count = 0
        self.analyzer = AnalyzerService()

    @rule(target=sensor_data, sensor_type=sensor_types, value=sensor_values)
    def add_sensor_reading(self, sensor_type, value):
        """Add a new sensor reading to the system."""
        assume(not (value != value))  # Exclude NaN values
        assume(value != float('inf') and value != float('-inf'))  # Exclude infinity
        
        return SensorData(
            sensor_id=f"{sensor_type}_sensor",
            value=value,
            timestamp="2024-01-01T10:00:00Z",
            sensor_type=sensor_type
        )

    @rule(target=analysis_results, data=st.lists(st.consumes(sensor_data), min_size=1, max_size=5))
    def analyze_sensor_data(self, data):
        """Analyze collected sensor data."""
        if not data:
            return None
            
        result = self.analyzer.analyze(data)
        
        # Update internal state tracking
        self.violation_count = len(result.get("violations", []))
        self.quality_score = result.get("quality_score", 1.0)
        self.system_state = result.get("state", SystemState.UNKNOWN)
        
        return result

    @invariant()
    def quality_score_bounds(self):
        """Quality score must always be between 0 and 1."""
        assert 0.0 <= self.quality_score <= 1.0

    @invariant()
    def state_violation_consistency(self):
        """System state should be consistent with violation count."""
        if self.violation_count == 0:
            assert self.system_state in [SystemState.NORMAL, SystemState.UNKNOWN]
        elif self.violation_count > 3:
            assert self.system_state in [SystemState.CRITICAL, SystemState.WARNING, SystemState.UNKNOWN]

    @invariant()
    def quality_score_violation_relationship(self):
        """Quality score should decrease with more violations."""
        expected_score = max(0.0, 1.0 - (self.violation_count * 0.15))
        # Allow for small floating point differences
        assert abs(self.quality_score - expected_score) < 0.001


# Test the state machine
TestMapeKStateMachine = MapeKStateMachine.TestCase


class TestBoundaryConditions:
    """Test system behavior at boundary conditions."""

    @pytest.mark.parametrize("boundary_value,sensor_type,expected_violation", [
        (0.0, "flow", False),
        (100.1, "flow", True),  # Just above threshold
        (99.9, "flow", False),  # Just below threshold
        (0.0, "pressure", False),
        (4.1, "pressure", True),  # Just above threshold
        (3.9, "pressure", False),  # Just below threshold
        (10.0, "quality", False),
        (5.9, "quality", True),  # Just below threshold
        (6.1, "quality", False),  # Just above threshold
    ])
    def test_threshold_boundary_detection(self, boundary_value, sensor_type, expected_violation):
        """Test threshold detection at exact boundary values."""
        # Arrange
        analyzer = AnalyzerService()
        sensor_data = [SensorData(
            sensor_id=f"{sensor_type}_sensor",
            value=boundary_value,
            timestamp="2024-01-01T10:00:00Z",
            sensor_type=sensor_type
        )]
        
        # Act
        result = analyzer.analyze(sensor_data)
        
        # Assert
        has_violation = len(result.get("violations", [])) > 0
        assert has_violation == expected_violation

    @given(
        sensor_count=st.integers(min_value=1, max_value=100),
        value_range=st.tuples(
            st.floats(min_value=0.0, max_value=50.0),
            st.floats(min_value=50.0, max_value=100.0)
        )
    )
    @settings(max_examples=20)
    def test_scaling_behavior(self, sensor_count, value_range):
        """Test system behavior with varying numbers of sensors."""
        # Arrange
        analyzer = AnalyzerService()
        min_val, max_val = value_range
        assume(min_val < max_val)
        
        sensor_data = []
        for i in range(sensor_count):
            value = min_val + (max_val - min_val) * (i / max(1, sensor_count - 1))
            sensor_data.append(SensorData(
                sensor_id=f"sensor_{i}",
                value=value,
                timestamp="2024-01-01T10:00:00Z",
                sensor_type="flow"
            ))
        
        # Act
        result = analyzer.analyze(sensor_data)
        
        # Assert
        assert result is not None
        assert "state" in result
        assert "quality_score" in result
        # With more sensors, we might detect more violations, but system should still function
        assert 0.0 <= result["quality_score"] <= 1.0
