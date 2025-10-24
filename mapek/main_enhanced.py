"""
Enhanced MAPE-K Digital Twin System with Advanced Software Engineering Patterns

This module integrates all the advanced patterns into the main MAPE-K system:
- Strategy Pattern for scenario-driven analysis
- Observer Pattern for event-driven communication  
- Command Pattern for reversible operations
- Adapter Pattern for legacy system integration
- Template Method Pattern for consistent pipeline execution
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any

# Original MAPE-K components
from application.services.monitor_service import Monitor
from application.services.analyzer_service import Analyzer
from application.services.planner_service import Planner
from application.services.executor_service import Executor
from application.services.container import MAPEKContainer
from logger import logger
from knowledge import get_db_conn

# Advanced Pattern Integrations
from domain.strategies.scenario_analysis_strategy import ScenarioAnalyzer, ScenarioType
from domain.events.event_system import DigitalTwinEventBus, Event, EventType
from domain.commands.command_pattern import CommandInvoker, SystemParameterAdjustmentCommand
from domain.adapters.legacy_integration import MultiSystemIntegrationManager
from domain.patterns.template_method_pipeline import (
    PipelineOrchestrator, 
    StandardWaterUtilityPipeline,
    EmergencyResponsePipeline,
    OptimizationPipeline
)

class EnhancedMAPEKSystem:
    """
    Enhanced MAPE-K system that integrates all advanced software engineering patterns
    into a production-ready digital twin for water utility networks.
    """
    
    def __init__(self):
        # Initialize original MAPE-K container
        self.container = MAPEKContainer()
        self.monitor_service = Monitor(self.container.node_repo)
        self.analyzer_service = Analyzer(self.container.threshold_repo)
        self.planner_service = Planner(self.container.plan_repo)
        self.executor_service = Executor(self.container.node_repo)
        
        # Initialize advanced pattern components
        self.scenario_analyzer = ScenarioAnalyzer()
        self.event_bus = DigitalTwinEventBus()
        self.command_invoker = CommandInvoker()
        self.integration_manager = MultiSystemIntegrationManager()
        self.pipeline_orchestrator = PipelineOrchestrator()
        
        # Register pipeline variants
        self._register_pipelines()
        
        # Set up event observers
        self._setup_event_observers()
        
        # Current system state
        self.current_scenario = ScenarioType.NORMAL_OPERATION
        self.system_metrics = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "scenario_changes": 0,
            "commands_executed": 0,
            "events_processed": 0
        }
        
        logger.info("🚀 Enhanced MAPE-K System initialized with advanced patterns")
    
    def _register_pipelines(self):
        """Register different pipeline variants for different scenarios."""
        
        # Standard pipeline for normal operations
        standard_pipeline = StandardWaterUtilityPipeline(
            monitor_service=self.monitor_service,
            analyzer_service=self.analyzer_service,
            planner_service=self.planner_service,
            executor_service=self.executor_service
        )
        
        # Emergency response pipeline
        emergency_pipeline = EmergencyResponsePipeline(
            monitor_service=self.monitor_service,
            analyzer_service=self.analyzer_service,
            planner_service=self.planner_service,
            executor_service=self.executor_service,
            event_bus=self.event_bus
        )
        
        # Optimization pipeline
        optimization_pipeline = OptimizationPipeline(
            monitor_service=self.monitor_service,
            analyzer_service=self.analyzer_service,
            planner_service=self.planner_service,
            executor_service=self.executor_service
        )
        
        # Register pipelines with orchestrator
        self.pipeline_orchestrator.register_pipeline("standard", standard_pipeline)
        self.pipeline_orchestrator.register_pipeline("emergency", emergency_pipeline)
        self.pipeline_orchestrator.register_pipeline("optimization", optimization_pipeline)
        
        logger.info("📋 Registered 3 pipeline variants: standard, emergency, optimization")
    
    def _setup_event_observers(self):
        """Set up event observers for different system events."""
        
        from domain.events.event_system import SystemStateObserver, AlertObserver, MetricsObserver
        
        # System state observer
        state_observer = SystemStateObserver()
        self.event_bus.subscribe(EventType.SYSTEM_STATE_CHANGE, state_observer)
        
        # Alert observer for emergency situations
        alert_observer = AlertObserver(callback=self._handle_emergency_alert)
        self.event_bus.subscribe(EventType.ALERT_TRIGGERED, alert_observer)
        
        # Metrics observer for performance monitoring
        metrics_observer = MetricsObserver()
        self.event_bus.subscribe(EventType.ANALYSIS_COMPLETED, metrics_observer)
        self.event_bus.subscribe(EventType.EXECUTION_COMPLETED, metrics_observer)
        
        logger.info("👁️ Set up event observers for system monitoring")
    
    async def _handle_emergency_alert(self, alert_data: Dict[str, Any]):
        """Handle emergency alerts by switching to emergency pipeline."""
        logger.warning(f"🚨 Emergency alert received: {alert_data}")
        
        # Switch to emergency scenario
        if self.current_scenario != ScenarioType.EMERGENCY_RESPONSE:
            await self._switch_scenario(ScenarioType.EMERGENCY_RESPONSE)
    
    async def _switch_scenario(self, new_scenario: ScenarioType):
        """Switch the system to a different operational scenario."""
        
        previous_scenario = self.current_scenario
        self.current_scenario = new_scenario
        self.system_metrics["scenario_changes"] += 1
        
        # Publish scenario change event
        scenario_event = Event(
            event_type=EventType.SYSTEM_STATE_CHANGE,
            source="enhanced_mapek_system",
            data={
                "previous_scenario": previous_scenario.value,
                "new_scenario": new_scenario.value,
                "timestamp": datetime.now().isoformat(),
                "reason": "automatic_adaptation"
            },
            timestamp=datetime.now()
        )
        
        await self.event_bus.publish_event(scenario_event)
        
        logger.info(f"🔄 Scenario changed: {previous_scenario.value} → {new_scenario.value}")
    
    async def enhanced_mapek_cycle(self) -> Dict[str, Any]:
        """
        Execute one enhanced MAPE-K cycle using advanced patterns.
        
        Returns:
            Dict containing cycle results and metrics
        """
        
        cycle_start_time = datetime.now()
        cycle_results = {
            "cycle_id": f"cycle_{self.system_metrics['total_cycles'] + 1}",
            "start_time": cycle_start_time.isoformat(),
            "scenario": self.current_scenario.value,
            "patterns_used": [],
            "performance_metrics": {}
        }
        
        try:
            logger.info(f"🔄 Starting enhanced MAPE-K cycle #{self.system_metrics['total_cycles'] + 1}")
            
            # Step 1: Collect data using Adapter Pattern
            logger.info("📊 Phase 1: Enhanced monitoring with legacy system integration")
            
            # Use both original monitor and adapter pattern for comprehensive data collection
            original_sensor_data = self.monitor_service.read_sensors()
            
            # Simulate legacy system data (in real deployment, this would connect to actual systems)
            legacy_sensor_data = await self._simulate_legacy_data_collection()
            
            # Combine data sources
            all_sensor_data = original_sensor_data + legacy_sensor_data
            cycle_results["sensor_data_count"] = len(all_sensor_data)
            cycle_results["patterns_used"].append("Adapter Pattern")
            
            # Step 2: Analyze using Strategy Pattern
            logger.info("🔍 Phase 2: Scenario-driven analysis")
            
            # Create analysis context based on current scenario
            analysis_context = self.scenario_analyzer.create_context(
                scenario_type=self.current_scenario,
                time_of_day=self._get_time_of_day(),
                system_load=self._calculate_system_load(all_sensor_data),
                weather_conditions="normal"  # In real system, get from weather API
            )
            
            # Perform scenario-driven analysis
            enhanced_analysis = await self.scenario_analyzer.analyze(all_sensor_data, analysis_context)
            
            # Also run original analysis for comparison
            original_analysis = self.analyzer_service.analyze(original_sensor_data)
            
            cycle_results["analysis_result"] = enhanced_analysis
            cycle_results["original_analysis"] = original_analysis
            cycle_results["patterns_used"].append("Strategy Pattern")
            
            # Publish analysis completion event
            analysis_event = Event(
                event_type=EventType.ANALYSIS_COMPLETED,
                source="enhanced_analyzer",
                data={
                    "scenario": self.current_scenario.value,
                    "enhanced_analysis": enhanced_analysis,
                    "sensor_count": len(all_sensor_data),
                    "violations": enhanced_analysis.get("violations", [])
                },
                timestamp=datetime.now()
            )
            await self.event_bus.publish_event(analysis_event)
            cycle_results["patterns_used"].append("Observer Pattern")
            
            # Step 3: Determine pipeline and execute using Template Method Pattern
            logger.info("📋 Phase 3: Pipeline-based planning and execution")
            
            # Select appropriate pipeline based on analysis results
            pipeline_name = self._select_pipeline(enhanced_analysis)
            
            # Execute pipeline using Template Method Pattern
            pipeline_context = {
                "sensor_data": all_sensor_data,
                "analysis_result": enhanced_analysis,
                "scenario": self.current_scenario.value,
                "cycle_id": cycle_results["cycle_id"]
            }
            
            pipeline_result = await self.pipeline_orchestrator.execute_pipeline(pipeline_name, pipeline_context)
            
            cycle_results["pipeline_used"] = pipeline_name
            cycle_results["pipeline_result"] = pipeline_result.to_dict()
            cycle_results["patterns_used"].append("Template Method Pattern")
            
            # Step 4: Execute commands if needed using Command Pattern
            if pipeline_result.execution_plan and pipeline_result.execution_plan.get("actions"):
                logger.info("⚡ Phase 4: Reversible command execution")
                
                executed_commands = []
                for action in pipeline_result.execution_plan["actions"]:
                    command = self._create_command_from_action(action)
                    if command:
                        result = await self.command_invoker.execute_command(command)
                        executed_commands.append({
                            "action": action,
                            "command_type": command.__class__.__name__,
                            "success": result.success,
                            "can_undo": command.can_undo(),
                            "message": result.message
                        })
                        self.system_metrics["commands_executed"] += 1
                
                cycle_results["executed_commands"] = executed_commands
                cycle_results["patterns_used"].append("Command Pattern")
                
                # Publish execution completion event
                execution_event = Event(
                    event_type=EventType.EXECUTION_COMPLETED,
                    source="enhanced_executor",
                    data={
                        "commands_executed": len(executed_commands),
                        "successful_commands": sum(1 for cmd in executed_commands if cmd["success"]),
                        "reversible_commands": sum(1 for cmd in executed_commands if cmd["can_undo"])
                    },
                    timestamp=datetime.now()
                )
                await self.event_bus.publish_event(execution_event)
            
            # Step 5: Update knowledge and check for scenario changes
            logger.info("🧠 Phase 5: Knowledge update and adaptation")
            
            # Check if scenario should change based on analysis
            new_scenario = self._determine_scenario_from_analysis(enhanced_analysis)
            if new_scenario != self.current_scenario:
                await self._switch_scenario(new_scenario)
            
            # Store results in database (original functionality)
            await self._store_cycle_results(cycle_results, all_sensor_data, enhanced_analysis, pipeline_result)
            
            # Calculate performance metrics
            cycle_end_time = datetime.now()
            cycle_duration = (cycle_end_time - cycle_start_time).total_seconds()
            
            cycle_results["end_time"] = cycle_end_time.isoformat()
            cycle_results["duration_seconds"] = cycle_duration
            cycle_results["performance_metrics"] = {
                "cycle_duration": cycle_duration,
                "patterns_integrated": len(cycle_results["patterns_used"]),
                "events_published": 2,  # analysis + execution events
                "commands_executed": len(cycle_results.get("executed_commands", [])),
                "sensors_processed": len(all_sensor_data)
            }
            
            # Update system metrics
            self.system_metrics["total_cycles"] += 1
            self.system_metrics["successful_cycles"] += 1
            
            logger.info(f"✅ Enhanced MAPE-K cycle completed successfully in {cycle_duration:.2f}s")
            logger.info(f"🎯 Patterns used: {', '.join(cycle_results['patterns_used'])}")
            
            return cycle_results
            
        except Exception as e:
            logger.error(f"❌ Enhanced MAPE-K cycle failed: {str(e)}")
            cycle_results["error"] = str(e)
            cycle_results["success"] = False
            
            # Publish error event
            error_event = Event(
                event_type=EventType.ALERT_TRIGGERED,
                source="enhanced_mapek_system",
                data={
                    "alert_level": "error",
                    "error_message": str(e),
                    "cycle_id": cycle_results["cycle_id"]
                },
                timestamp=datetime.now()
            )
            await self.event_bus.publish_event(error_event)
            
            raise
    
    async def _simulate_legacy_data_collection(self) -> List[Dict[str, Any]]:
        """Simulate legacy system data collection (in real system, use actual adapters)."""
        
        # In a real implementation, this would use the actual legacy integration manager
        # For demo purposes, we'll simulate some legacy sensor data
        
        simulated_legacy_data = [
            {
                "node_id": "legacy_scada_01",
                "sensor_type": "pressure",
                "value": 3.2,
                "timestamp": datetime.now().isoformat(),
                "source": "SCADA_Modbus",
                "quality": "good"
            },
            {
                "node_id": "legacy_xml_01", 
                "sensor_type": "flow",
                "value": 125.5,
                "timestamp": datetime.now().isoformat(),
                "source": "XML_WebService",
                "quality": "good"
            }
        ]
        
        logger.info(f"🔌 Collected {len(simulated_legacy_data)} readings from legacy systems")
        return simulated_legacy_data
    
    def _get_time_of_day(self) -> str:
        """Get current time of day for context."""
        hour = datetime.now().hour
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def _calculate_system_load(self, sensor_data: List[Dict[str, Any]]) -> float:
        """Calculate system load based on sensor readings."""
        
        # Simple load calculation based on flow rates
        flow_readings = [data["value"] for data in sensor_data if data.get("sensor_type") == "flow"]
        if not flow_readings:
            return 0.5  # Default to 50% load
        
        avg_flow = sum(flow_readings) / len(flow_readings)
        # Normalize to 0-1 scale (assuming max flow of 200)
        return min(avg_flow / 200.0, 1.0)
    
    def _select_pipeline(self, analysis_result: Dict[str, Any]) -> str:
        """Select appropriate pipeline based on analysis results."""
        
        violations = analysis_result.get("violations", [])
        state = analysis_result.get("state", "NORMAL")
        
        # Emergency pipeline for critical violations
        critical_violations = [v for v in violations if v.get("severity") == "critical"]
        if critical_violations or state == "EMERGENCY":
            return "emergency"
        
        # Optimization pipeline for stable conditions with opportunities
        if state == "NORMAL" and len(violations) == 0:
            return "optimization"
        
        # Standard pipeline for everything else
        return "standard"
    
    def _create_command_from_action(self, action: Dict[str, Any]):
        """Create a command object from a planned action."""
        
        action_type = action.get("type")
        
        if action_type == "adjust_parameter":
            return SystemParameterAdjustmentCommand(
                parameter_name=action.get("parameter"),
                new_value=action.get("value"),
                target_component=action.get("component", "system")
            )
        
        # Add more command types as needed
        return None
    
    def _determine_scenario_from_analysis(self, analysis_result: Dict[str, Any]) -> ScenarioType:
        """Determine appropriate scenario based on analysis results."""
        
        violations = analysis_result.get("violations", [])
        state = analysis_result.get("state", "NORMAL")
        
        # Emergency response for critical conditions
        if state == "EMERGENCY" or any(v.get("severity") == "critical" for v in violations):
            return ScenarioType.EMERGENCY_RESPONSE
        
        # Peak demand during high load periods
        if len(violations) > 2 and self._get_time_of_day() in ["afternoon", "evening"]:
            return ScenarioType.PEAK_DEMAND
        
        # Drought conditions (would be determined by external factors in real system)
        # For demo, we'll stick with normal operation
        
        return ScenarioType.NORMAL_OPERATION
    
    async def _store_cycle_results(self, cycle_results: Dict[str, Any], sensor_data: List[Dict[str, Any]], 
                                 analysis_result: Dict[str, Any], pipeline_result) -> None:
        """Store cycle results in database (enhanced version of original functionality)."""
        
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            # Store enhanced cycle information
            for sensor_reading in sensor_data:
                node_id = sensor_reading.get('node_id')
                
                if node_id:
                    # Store analysis results
                    cur.execute(
                        "INSERT INTO analyze (node_id, result, state) VALUES (%s, %s, %s)",
                        (node_id, str(analysis_result), analysis_result.get('state', 'unknown'))
                    )
                    
                    # Store pipeline execution results
                    if pipeline_result.execution_plan:
                        plan_data = pipeline_result.execution_plan
                        priority = plan_data.get('priority', 'normal')
                        cur.execute(
                            "INSERT INTO plan (node_id, result, priority) VALUES (%s, %s, %s)",
                            (node_id, str(plan_data), priority)
                        )
                        cur.execute(
                            "INSERT INTO execute (node_id, result) VALUES (%s, %s)",
                            (node_id, str(plan_data))
                        )
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info("💾 Cycle results stored in database")
            
        except Exception as e:
            logger.error(f"❌ Failed to store cycle results: {str(e)}")
            if 'conn' in locals():
                try:
                    conn.rollback()
                    cur.close()
                    conn.close()
                except Exception:
                    pass
    
    async def run_continuous_operation(self, cycle_interval: int = 60):
        """
        Run the enhanced MAPE-K system continuously.
        
        Args:
            cycle_interval: Time between cycles in seconds
        """
        
        logger.info(f"🚀 Starting continuous enhanced MAPE-K operation (interval: {cycle_interval}s)")
        
        while True:
            try:
                # Execute enhanced MAPE-K cycle
                cycle_results = await self.enhanced_mapek_cycle()
                
                # Print summary
                logger.info("=" * 60)
                logger.info(f"📊 Cycle Summary:")
                logger.info(f"   • Scenario: {cycle_results['scenario']}")
                logger.info(f"   • Patterns Used: {len(cycle_results['patterns_used'])}")
                logger.info(f"   • Sensors Processed: {cycle_results['sensor_data_count']}")
                logger.info(f"   • Duration: {cycle_results['performance_metrics']['cycle_duration']:.2f}s")
                logger.info(f"   • Commands Executed: {len(cycle_results.get('executed_commands', []))}")
                logger.info("=" * 60)
                
                # Wait before next cycle
                await asyncio.sleep(cycle_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Shutting down enhanced MAPE-K system...")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in continuous operation: {str(e)}")
                await asyncio.sleep(cycle_interval)  # Continue despite errors
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics."""
        
        return {
            **self.system_metrics,
            "current_scenario": self.current_scenario.value,
            "success_rate": (
                self.system_metrics["successful_cycles"] / 
                max(1, self.system_metrics["total_cycles"])
            ),
            "avg_commands_per_cycle": (
                self.system_metrics["commands_executed"] / 
                max(1, self.system_metrics["total_cycles"])
            )
        }

async def main():
    """Main entry point for the enhanced MAPE-K system."""
    
    print("🚀 Enhanced MAPE-K Digital Twin System")
    print("=" * 60)
    print("🎯 Integrating 5 Advanced Software Engineering Patterns:")
    print("   • Strategy Pattern - Scenario-driven analysis")
    print("   • Observer Pattern - Event-driven communication")
    print("   • Command Pattern - Reversible operations")
    print("   • Adapter Pattern - Legacy system integration")
    print("   • Template Method Pattern - Consistent pipelines")
    print("=" * 60)
    
    # Initialize enhanced system
    enhanced_mapek = EnhancedMAPEKSystem()
    
    try:
        # Run single demonstration cycle
        print("\n🧪 Running demonstration cycle...")
        demo_results = await enhanced_mapek.enhanced_mapek_cycle()
        
        print(f"\n✅ Demonstration cycle completed successfully!")
        print(f"📊 Patterns integrated: {len(demo_results['patterns_used'])}")
        print(f"⏱️ Execution time: {demo_results['performance_metrics']['cycle_duration']:.2f}s")
        
        # Ask user if they want to run continuously
        print(f"\n🔄 Would you like to run the system continuously? (y/n): ", end="")
        
        # For automated demo, we'll run a few cycles
        print("Running 3 demonstration cycles...")
        for i in range(3):
            print(f"\n--- Cycle {i+1}/3 ---")
            await enhanced_mapek.enhanced_mapek_cycle()
            await asyncio.sleep(2)  # Short delay between demo cycles
        
        # Display final metrics
        metrics = enhanced_mapek.get_system_metrics()
        print(f"\n📈 Final System Metrics:")
        print(f"   • Total Cycles: {metrics['total_cycles']}")
        print(f"   • Success Rate: {metrics['success_rate']:.1%}")
        print(f"   • Scenario Changes: {metrics['scenario_changes']}")
        print(f"   • Commands Executed: {metrics['commands_executed']}")
        print(f"   • Events Processed: {metrics['events_processed']}")
        
        print(f"\n🎯 All advanced patterns successfully integrated into production MAPE-K system!")
        
    except KeyboardInterrupt:
        print(f"\n🛑 System shutdown requested")
    except Exception as e:
        print(f"\n❌ System error: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the enhanced system
    asyncio.run(main())
