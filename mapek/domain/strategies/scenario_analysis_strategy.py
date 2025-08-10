"""
Strategy Pattern Implementation for Scenario-Driven Digital Twin Analysis
Supports multiple analysis strategies for different water utility scenarios.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from domain.models import SensorData, SystemState
from domain.entities import ThresholdViolationType


class ScenarioType(Enum):
    """Different operational scenarios for water utility systems."""
    NORMAL_OPERATION = "normal_operation"
    PEAK_DEMAND = "peak_demand"
    MAINTENANCE_MODE = "maintenance_mode"
    EMERGENCY_RESPONSE = "emergency_response"
    DROUGHT_CONDITIONS = "drought_conditions"
    FLOOD_RESPONSE = "flood_response"
    NIGHT_MODE = "night_mode"
    INDUSTRIAL_PEAK = "industrial_peak"


@dataclass
class AnalysisContext:
    """Context information for analysis strategies."""
    scenario: ScenarioType
    time_of_day: str
    season: str
    weather_conditions: Dict[str, Any]
    system_load: float
    maintenance_schedule: List[str]
    historical_patterns: Dict[str, float]


class AnalysisStrategy(ABC):
    """Abstract base class for analysis strategies."""
    
    @abstractmethod
    def analyze(self, sensor_data: List[SensorData], context: AnalysisContext) -> Dict[str, Any]:
        """Perform analysis based on the specific strategy."""
        pass
    
    @abstractmethod
    def get_thresholds(self, sensor_type: str, context: AnalysisContext) -> Dict[str, float]:
        """Get dynamic thresholds based on context."""
        pass
    
    @abstractmethod
    def calculate_risk_score(self, violations: List[ThresholdViolationType], context: AnalysisContext) -> float:
        """Calculate risk score based on violations and context."""
        pass


class NormalOperationStrategy(AnalysisStrategy):
    """Analysis strategy for normal operational conditions."""
    
    def analyze(self, sensor_data: List[SensorData], context: AnalysisContext) -> Dict[str, Any]:
        """Standard analysis for normal operations."""
        violations = []
        total_sensors = len(sensor_data)
        quality_score = 1.0
        
        for data in sensor_data:
            thresholds = self.get_thresholds(data.sensor_type, context)
            
            if data.sensor_type == "flow" and data.value > thresholds["max_flow"]:
                violations.append(ThresholdViolationType.HIGH_FLOW)
            elif data.sensor_type == "pressure" and data.value > thresholds["max_pressure"]:
                violations.append(ThresholdViolationType.HIGH_PRESSURE)
            elif data.sensor_type == "quality" and data.value < thresholds["min_quality"]:
                violations.append(ThresholdViolationType.POOR_QUALITY)
        
        # Standard quality calculation
        violation_penalty = len(violations) * 0.15
        quality_score = max(0.0, 1.0 - violation_penalty)
        
        # Determine system state
        if len(violations) == 0:
            state = SystemState.NORMAL
        elif len(violations) <= 2:
            state = SystemState.WARNING
        else:
            state = SystemState.CRITICAL
        
        return {
            "state": state,
            "violations": violations,
            "quality_score": quality_score,
            "risk_score": self.calculate_risk_score(violations, context),
            "strategy_used": "normal_operation",
            "total_sensors_analyzed": total_sensors
        }
    
    def get_thresholds(self, sensor_type: str, context: AnalysisContext) -> Dict[str, float]:
        """Get standard thresholds for normal operation."""
        base_thresholds = {
            "flow": {"min_flow": 0, "max_flow": 100},
            "pressure": {"min_pressure": 0, "max_pressure": 4.0},
            "quality": {"min_quality": 6.0, "max_quality": 10.0},
            "temperature": {"min_temperature": 5.0, "max_temperature": 25.0}
        }
        return base_thresholds.get(sensor_type, {})
    
    def calculate_risk_score(self, violations: List[ThresholdViolationType], context: AnalysisContext) -> float:
        """Calculate standard risk score."""
        base_risk = len(violations) * 0.2
        return min(1.0, base_risk)


class PeakDemandStrategy(AnalysisStrategy):
    """Analysis strategy for peak demand periods."""
    
    def analyze(self, sensor_data: List[SensorData], context: AnalysisContext) -> Dict[str, Any]:
        """Enhanced analysis for peak demand scenarios."""
        violations = []
        total_sensors = len(sensor_data)
        quality_score = 1.0
        
        # Peak demand analysis considers system load
        load_factor = context.system_load / 100.0  # Normalize load percentage
        
        for data in sensor_data:
            thresholds = self.get_thresholds(data.sensor_type, context)
            
            # Adjusted thresholds for peak demand
            if data.sensor_type == "flow":
                # Allow higher flow during peak demand
                adjusted_max = thresholds["max_flow"] * (1.0 + load_factor * 0.3)
                if data.value > adjusted_max:
                    violations.append(ThresholdViolationType.HIGH_FLOW)
            elif data.sensor_type == "pressure":
                # More sensitive to pressure during peak demand
                adjusted_max = thresholds["max_pressure"] * (1.0 - load_factor * 0.1)
                if data.value > adjusted_max:
                    violations.append(ThresholdViolationType.HIGH_PRESSURE)
            elif data.sensor_type == "quality":
                # Quality becomes more critical during peak demand
                adjusted_min = thresholds["min_quality"] * (1.0 + load_factor * 0.05)
                if data.value < adjusted_min:
                    violations.append(ThresholdViolationType.POOR_QUALITY)
        
        # Peak demand penalty calculation
        violation_penalty = len(violations) * 0.20  # Higher penalty during peak
        load_penalty = max(0, (load_factor - 0.8) * 0.2)  # Penalty for very high load
        quality_score = max(0.0, 1.0 - violation_penalty - load_penalty)
        
        # State determination considers load
        if len(violations) == 0 and load_factor < 0.8:
            state = SystemState.NORMAL
        elif len(violations) <= 1 and load_factor < 0.9:
            state = SystemState.WARNING
        else:
            state = SystemState.CRITICAL
        
        return {
            "state": state,
            "violations": violations,
            "quality_score": quality_score,
            "risk_score": self.calculate_risk_score(violations, context),
            "strategy_used": "peak_demand",
            "system_load_factor": load_factor,
            "load_adjusted_thresholds": True,
            "total_sensors_analyzed": total_sensors
        }
    
    def get_thresholds(self, sensor_type: str, context: AnalysisContext) -> Dict[str, float]:
        """Get adjusted thresholds for peak demand."""
        load_factor = context.system_load / 100.0
        
        base_thresholds = {
            "flow": {"min_flow": 0, "max_flow": 100 * (1.0 + load_factor * 0.3)},
            "pressure": {"min_pressure": 0, "max_pressure": 4.0 * (1.0 - load_factor * 0.1)},
            "quality": {"min_quality": 6.0 * (1.0 + load_factor * 0.05), "max_quality": 10.0},
            "temperature": {"min_temperature": 5.0, "max_temperature": 25.0 + load_factor * 5}
        }
        return base_thresholds.get(sensor_type, {})
    
    def calculate_risk_score(self, violations: List[ThresholdViolationType], context: AnalysisContext) -> float:
        """Calculate risk score with peak demand considerations."""
        base_risk = len(violations) * 0.25  # Higher base risk during peak
        load_risk = max(0, (context.system_load / 100.0 - 0.8) * 0.3)
        return min(1.0, base_risk + load_risk)


class EmergencyResponseStrategy(AnalysisStrategy):
    """Analysis strategy for emergency response scenarios."""
    
    def analyze(self, sensor_data: List[SensorData], context: AnalysisContext) -> Dict[str, Any]:
        """Critical analysis for emergency scenarios."""
        violations = []
        critical_violations = []
        total_sensors = len(sensor_data)
        
        for data in sensor_data:
            thresholds = self.get_thresholds(data.sensor_type, context)
            
            # Emergency thresholds are much tighter
            if data.sensor_type == "flow":
                if data.value > thresholds["critical_max_flow"]:
                    critical_violations.append(ThresholdViolationType.HIGH_FLOW)
                elif data.value > thresholds["max_flow"]:
                    violations.append(ThresholdViolationType.HIGH_FLOW)
            elif data.sensor_type == "pressure":
                if data.value > thresholds["critical_max_pressure"]:
                    critical_violations.append(ThresholdViolationType.HIGH_PRESSURE)
                elif data.value > thresholds["max_pressure"]:
                    violations.append(ThresholdViolationType.HIGH_PRESSURE)
            elif data.sensor_type == "quality":
                if data.value < thresholds["critical_min_quality"]:
                    critical_violations.append(ThresholdViolationType.POOR_QUALITY)
                elif data.value < thresholds["min_quality"]:
                    violations.append(ThresholdViolationType.POOR_QUALITY)
        
        # Emergency quality calculation
        all_violations = violations + critical_violations
        critical_penalty = len(critical_violations) * 0.4  # Severe penalty for critical violations
        violation_penalty = len(violations) * 0.25
        quality_score = max(0.0, 1.0 - critical_penalty - violation_penalty)
        
        # In emergency mode, any critical violation triggers CRITICAL state
        if len(critical_violations) > 0:
            state = SystemState.CRITICAL
        elif len(violations) > 0:
            state = SystemState.WARNING
        else:
            state = SystemState.NORMAL
        
        return {
            "state": state,
            "violations": violations,
            "critical_violations": critical_violations,
            "quality_score": quality_score,
            "risk_score": self.calculate_risk_score(all_violations, context),
            "strategy_used": "emergency_response",
            "emergency_mode_active": True,
            "total_sensors_analyzed": total_sensors,
            "critical_threshold_breaches": len(critical_violations)
        }
    
    def get_thresholds(self, sensor_type: str, context: AnalysisContext) -> Dict[str, float]:
        """Get emergency thresholds with critical limits."""
        emergency_thresholds = {
            "flow": {
                "min_flow": 0, 
                "max_flow": 80,  # Reduced from normal 100
                "critical_max_flow": 120  # Emergency shutdown level
            },
            "pressure": {
                "min_pressure": 0, 
                "max_pressure": 3.0,  # Reduced from normal 4.0
                "critical_max_pressure": 5.0  # Emergency shutdown level
            },
            "quality": {
                "min_quality": 7.0,  # Increased from normal 6.0
                "critical_min_quality": 4.0,  # Emergency contamination level
                "max_quality": 10.0
            },
            "temperature": {
                "min_temperature": 8.0,  # Increased from normal 5.0
                "max_temperature": 20.0,  # Reduced from normal 25.0
                "critical_max_temperature": 35.0
            }
        }
        return emergency_thresholds.get(sensor_type, {})
    
    def calculate_risk_score(self, violations: List[ThresholdViolationType], context: AnalysisContext) -> float:
        """Calculate elevated risk score for emergency scenarios."""
        base_risk = len(violations) * 0.4  # Very high base risk in emergency
        emergency_multiplier = 1.5  # Emergency scenarios are inherently riskier
        return min(1.0, base_risk * emergency_multiplier)


class DroughtConditionsStrategy(AnalysisStrategy):
    """Analysis strategy for drought conditions."""
    
    def analyze(self, sensor_data: List[SensorData], context: AnalysisContext) -> Dict[str, Any]:
        """Conservation-focused analysis for drought conditions."""
        violations = []
        conservation_violations = []
        total_sensors = len(sensor_data)
        
        # Get drought severity from context
        drought_severity = context.weather_conditions.get("drought_severity", 0.5)  # 0-1 scale
        
        for data in sensor_data:
            thresholds = self.get_thresholds(data.sensor_type, context)
            
            if data.sensor_type == "flow":
                # Much lower flow thresholds during drought
                conservation_limit = thresholds["conservation_max_flow"]
                normal_limit = thresholds["max_flow"]
                
                if data.value > normal_limit:
                    violations.append(ThresholdViolationType.HIGH_FLOW)
                elif data.value > conservation_limit:
                    conservation_violations.append("FLOW_CONSERVATION_EXCEEDED")
                    
            elif data.sensor_type == "pressure":
                # Maintain minimum pressure for safety
                if data.value < thresholds["min_pressure"]:
                    violations.append(ThresholdViolationType.LOW_PRESSURE)
                elif data.value > thresholds["max_pressure"]:
                    violations.append(ThresholdViolationType.HIGH_PRESSURE)
                    
            elif data.sensor_type == "quality":
                # Quality becomes more important when water is scarce
                enhanced_min = thresholds["enhanced_min_quality"]
                if data.value < enhanced_min:
                    violations.append(ThresholdViolationType.POOR_QUALITY)
        
        # Drought-specific quality calculation
        all_violations = violations + conservation_violations
        conservation_penalty = len(conservation_violations) * 0.1
        violation_penalty = len(violations) * 0.2
        drought_penalty = drought_severity * 0.1  # Base penalty for drought conditions
        
        quality_score = max(0.0, 1.0 - violation_penalty - conservation_penalty - drought_penalty)
        
        # State determination considers conservation
        if len(violations) == 0 and len(conservation_violations) <= 1:
            state = SystemState.NORMAL
        elif len(violations) <= 1 and len(conservation_violations) <= 3:
            state = SystemState.WARNING
        else:
            state = SystemState.CRITICAL
        
        return {
            "state": state,
            "violations": violations,
            "conservation_violations": conservation_violations,
            "quality_score": quality_score,
            "risk_score": self.calculate_risk_score(violations, context),
            "strategy_used": "drought_conditions",
            "drought_severity": drought_severity,
            "conservation_mode_active": True,
            "total_sensors_analyzed": total_sensors,
            "water_conservation_score": 1.0 - (len(conservation_violations) * 0.2)
        }
    
    def get_thresholds(self, sensor_type: str, context: AnalysisContext) -> Dict[str, float]:
        """Get conservation-focused thresholds for drought conditions."""
        drought_severity = context.weather_conditions.get("drought_severity", 0.5)
        conservation_factor = 1.0 - (drought_severity * 0.4)  # Reduce limits during drought
        
        drought_thresholds = {
            "flow": {
                "min_flow": 0,
                "conservation_max_flow": 60 * conservation_factor,  # Conservation limit
                "max_flow": 80 * conservation_factor,  # Reduced from normal 100
            },
            "pressure": {
                "min_pressure": 2.0,  # Minimum for safety
                "max_pressure": 4.0,
            },
            "quality": {
                "enhanced_min_quality": 7.5,  # Higher quality standards when water is scarce
                "min_quality": 6.5,
                "max_quality": 10.0
            },
            "temperature": {
                "min_temperature": 5.0,
                "max_temperature": 30.0  # Allow higher temps to reduce cooling energy
            }
        }
        return drought_thresholds.get(sensor_type, {})
    
    def calculate_risk_score(self, violations: List[ThresholdViolationType], context: AnalysisContext) -> float:
        """Calculate risk score considering drought conditions."""
        base_risk = len(violations) * 0.25
        drought_risk = context.weather_conditions.get("drought_severity", 0.0) * 0.3
        return min(1.0, base_risk + drought_risk)


class ScenarioAnalyzer:
    """Context class that uses different analysis strategies based on scenario."""
    
    def __init__(self):
        self.strategies = {
            ScenarioType.NORMAL_OPERATION: NormalOperationStrategy(),
            ScenarioType.PEAK_DEMAND: PeakDemandStrategy(),
            ScenarioType.EMERGENCY_RESPONSE: EmergencyResponseStrategy(),
            ScenarioType.DROUGHT_CONDITIONS: DroughtConditionsStrategy(),
            # Add more strategies as needed
        }
        self.current_strategy: Optional[AnalysisStrategy] = None
        self.current_context: Optional[AnalysisContext] = None
    
    def set_scenario(self, scenario: ScenarioType, context: AnalysisContext) -> None:
        """Set the current scenario and context."""
        if scenario not in self.strategies:
            raise ValueError(f"No strategy available for scenario: {scenario}")
        
        self.current_strategy = self.strategies[scenario]
        self.current_context = context
    
    def analyze(self, sensor_data: List[SensorData]) -> Dict[str, Any]:
        """Perform analysis using the current strategy."""
        if not self.current_strategy or not self.current_context:
            raise ValueError("No strategy or context set. Call set_scenario() first.")
        
        result = self.current_strategy.analyze(sensor_data, self.current_context)
        
        # Add metadata about the analysis
        result.update({
            "scenario_type": self.current_context.scenario.value,
            "analysis_timestamp": self.current_context.time_of_day,
            "context_metadata": {
                "season": self.current_context.season,
                "weather": self.current_context.weather_conditions,
                "system_load": self.current_context.system_load
            }
        })
        
        return result
    
    def get_available_scenarios(self) -> List[ScenarioType]:
        """Get list of available scenario types."""
        return list(self.strategies.keys())
    
    def add_strategy(self, scenario: ScenarioType, strategy: AnalysisStrategy) -> None:
        """Add a new analysis strategy for a scenario."""
        self.strategies[scenario] = strategy
    
    def get_scenario_recommendations(self, current_conditions: Dict[str, Any]) -> ScenarioType:
        """Recommend appropriate scenario based on current conditions."""
        # Simple rule-based scenario selection
        # In a real system, this could use ML or more complex logic
        
        system_load = current_conditions.get("system_load", 50)
        emergency_status = current_conditions.get("emergency_active", False)
        drought_level = current_conditions.get("drought_severity", 0.0)
        time_of_day = current_conditions.get("time_of_day", "12:00")
        
        if emergency_status:
            return ScenarioType.EMERGENCY_RESPONSE
        elif drought_level > 0.3:
            return ScenarioType.DROUGHT_CONDITIONS
        elif system_load > 80:
            return ScenarioType.PEAK_DEMAND
        elif "night" in time_of_day.lower():
            return ScenarioType.NIGHT_MODE
        else:
            return ScenarioType.NORMAL_OPERATION


# Factory class for creating analysis contexts
class AnalysisContextFactory:
    """Factory for creating analysis contexts based on real-time conditions."""
    
    @staticmethod
    def create_context(
        scenario: ScenarioType,
        system_conditions: Dict[str, Any],
        external_conditions: Dict[str, Any]
    ) -> AnalysisContext:
        """Create an analysis context from system and external conditions."""
        
        return AnalysisContext(
            scenario=scenario,
            time_of_day=system_conditions.get("time_of_day", "12:00"),
            season=external_conditions.get("season", "summer"),
            weather_conditions=external_conditions.get("weather", {}),
            system_load=system_conditions.get("load_percentage", 50.0),
            maintenance_schedule=system_conditions.get("maintenance_items", []),
            historical_patterns=system_conditions.get("historical_data", {})
        )
    
    @staticmethod
    def create_emergency_context(emergency_type: str, severity: float) -> AnalysisContext:
        """Create an emergency analysis context."""
        return AnalysisContext(
            scenario=ScenarioType.EMERGENCY_RESPONSE,
            time_of_day="emergency",
            season="emergency",
            weather_conditions={"emergency_type": emergency_type, "severity": severity},
            system_load=100.0,  # Assume high load during emergency
            maintenance_schedule=[],
            historical_patterns={}
        )
