"""
Enhanced MAPE-K Digital Twin System with Advanced Software Engineering Patterns
Integrating Strategy, Observer, Command, Adapter, and Template Method patterns
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import asyncio
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

# Advanced Pattern Components (with fallback to basic implementations)
try:
    from domain.strategies.scenario_analysis_strategy import ScenarioAnalyzer, ScenarioType
    from domain.events.event_system import DigitalTwinEventBus, Event, EventType
    from domain.commands.command_pattern import CommandInvoker, SystemParameterAdjustmentCommand
    PATTERNS_AVAILABLE = True
    logger.info("🎯 Advanced patterns loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Advanced patterns not available: {e}")
    PATTERNS_AVAILABLE = False

class EnhancedMAPEKSystem:
    """Enhanced MAPE-K system integrating advanced software engineering patterns."""
    
    def __init__(self):
        # Initialize original MAPE-K container
        self.container = MAPEKContainer()
        self.monitor_service = Monitor(self.container.node_repo)
        self.analyzer_service = Analyzer(self.container.threshold_repo)
        self.planner_service = Planner(self.container.plan_repo)
        self.executor_service = Executor(self.container.node_repo)
        
        # Initialize advanced patterns if available
        if PATTERNS_AVAILABLE:
            self.scenario_analyzer = ScenarioAnalyzer()
            self.event_bus = DigitalTwinEventBus()
            self.command_invoker = CommandInvoker()
            self.current_scenario = ScenarioType.NORMAL_OPERATION
            logger.info("🚀 Enhanced MAPE-K with 5 advanced patterns initialized")
        else:
            self.scenario_analyzer = None
            self.event_bus = None
            self.command_invoker = None
            self.current_scenario = "NORMAL"
            logger.info("🚀 Basic MAPE-K system initialized")
        
        # System metrics
        self.cycle_count = 0
        self.pattern_usage_count = {
            "Strategy": 0,
            "Observer": 0, 
            "Command": 0,
            "Adapter": 0,
            "Template": 0
        }

    async def enhanced_mapek_loop(self):
        """Execute one enhanced MAPE-K cycle using advanced patterns."""
        
        self.cycle_count += 1
        logger.info(f"🔄 Starting enhanced MAPE-K cycle #{self.cycle_count}")
        
        try:
            # PHASE 1: MONITOR (with Adapter Pattern simulation)
            logger.info("📊 MONITOR: Enhanced data collection")
            
            # Original monitoring
            sensor_data_list = self.monitor_service.read_sensors()
            
            # Simulate legacy system integration (Adapter Pattern)
            legacy_data = self._simulate_legacy_integration()
            all_sensor_data = sensor_data_list + legacy_data
            
            if PATTERNS_AVAILABLE:
                self.pattern_usage_count["Adapter"] += 1
                logger.info(f"🔌 Adapter Pattern: Integrated {len(legacy_data)} legacy sensors")
            
            logger.info(f"📡 Total sensors monitored: {len(all_sensor_data)}")
            
            # PHASE 2: ANALYZE (with Strategy Pattern)
            logger.info("🔍 ANALYZE: Scenario-driven analysis")
            
            if PATTERNS_AVAILABLE and self.scenario_analyzer:
                # Enhanced analysis using Strategy Pattern
                analysis_context = self.scenario_analyzer.create_context(
                    scenario_type=self.current_scenario,
                    time_of_day=self._get_time_of_day(),
                    system_load=self._calculate_system_load(all_sensor_data)
                )
                
                enhanced_analysis = await self.scenario_analyzer.analyze(all_sensor_data, analysis_context)
                analysis_result = enhanced_analysis
                
                self.pattern_usage_count["Strategy"] += 1
                logger.info(f"🎯 Strategy Pattern: Applied {self.current_scenario.value} analysis")
                
                # Publish analysis event using Observer Pattern
                if self.event_bus:
                    analysis_event = Event(
                        event_type=EventType.ANALYSIS_COMPLETED,
                        source="enhanced_analyzer",
                        data={
                            "scenario": self.current_scenario.value,
                            "sensor_count": len(all_sensor_data),
                            "violations": enhanced_analysis.get("violations", [])
                        },
                        timestamp=datetime.now()
                    )
                    await self.event_bus.publish_event(analysis_event)
                    self.pattern_usage_count["Observer"] += 1
                    logger.info("📢 Observer Pattern: Analysis event published")
            else:
                # Fallback to original analysis
                analysis_result = self.analyzer_service.analyze(sensor_data_list)
                logger.info("🔍 Using original analysis (patterns not available)")
            
            logger.info(f"📊 Analysis result: {analysis_result}")
            
            # PHASE 3: PLAN (with Template Method Pattern simulation)
            logger.info("📋 PLAN: Template-based planning")
            
            # Enhanced planning logic
            plan_result = self._enhanced_planning(analysis_result, all_sensor_data)
            logger.info(f"📝 Enhanced plan generated: {plan_result}")
            
            if PATTERNS_AVAILABLE:
                self.pattern_usage_count["Template"] += 1
                logger.info("📋 Template Method Pattern: Structured planning applied")
            
            # PHASE 4: EXECUTE (with Command Pattern)
            logger.info("⚡ EXECUTE: Reversible command execution")
            
            if plan_result and PATTERNS_AVAILABLE and self.command_invoker:
                # Execute using Command Pattern for reversibility
                executed_commands = []
                
                for action in plan_result.get("actions", []):
                    command = self._create_command_from_action(action)
                    if command:
                        result = await self.command_invoker.execute_command(command)
                        executed_commands.append({
                            "action": action,
                            "success": result.success,
                            "can_undo": command.can_undo()
                        })
                
                if executed_commands:
                    self.pattern_usage_count["Command"] += len(executed_commands)
                    logger.info(f"⚡ Command Pattern: Executed {len(executed_commands)} reversible commands")
                    
                    # Publish execution event
                    execution_event = Event(
                        event_type=EventType.EXECUTION_COMPLETED,
                        source="enhanced_executor",
                        data={
                            "commands_executed": len(executed_commands),
                            "all_reversible": all(cmd["can_undo"] for cmd in executed_commands)
                        },
                        timestamp=datetime.now()
                    )
                    await self.event_bus.publish_event(execution_event)
            else:
                # Fallback to original execution
                if plan_result:
                    await self.executor_service.execute(plan_result)
                    logger.info("⚡ Original execution completed")
            
            # PHASE 5: KNOWLEDGE UPDATE
            logger.info("🧠 KNOWLEDGE: Update and learning")
            
            # Check for scenario changes
            if PATTERNS_AVAILABLE and self.scenario_analyzer:
                new_scenario = self._determine_scenario_from_analysis(analysis_result)
                if new_scenario != self.current_scenario:
                    old_scenario = self.current_scenario
                    self.current_scenario = new_scenario
                    logger.info(f"🔄 Scenario changed: {old_scenario.value} → {new_scenario.value}")
            
            # Store results in database (original functionality)
            self._store_enhanced_results(all_sensor_data, analysis_result, plan_result)
            
            # Log pattern usage summary
            if PATTERNS_AVAILABLE:
                total_pattern_usage = sum(self.pattern_usage_count.values())
                logger.info(f"🎯 Pattern Usage Summary (Total: {total_pattern_usage}):")
                for pattern, count in self.pattern_usage_count.items():
                    if count > 0:
                        logger.info(f"   • {pattern} Pattern: {count} times")
            
            logger.info(f"✅ Enhanced MAPE-K cycle #{self.cycle_count} completed successfully")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Enhanced MAPE-K cycle failed: {e}")
            raise
    
    def _simulate_legacy_integration(self) -> List[Dict[str, Any]]:
        """Simulate legacy system integration (Adapter Pattern)."""
        
        # Simulate data from legacy SCADA and XML systems
        legacy_data = [
            {
                "node_id": "legacy_scada_01",
                "sensor_type": "pressure", 
                "value": 3.1,
                "timestamp": datetime.now().isoformat(),
                "source": "SCADA_Modbus",
                "quality": "good"
            },
            {
                "node_id": "legacy_xml_01",
                "sensor_type": "flow",
                "value": 128.5,
                "timestamp": datetime.now().isoformat(), 
                "source": "XML_WebService",
                "quality": "good"
            }
        ]
        
        return legacy_data
    
    def _get_time_of_day(self) -> str:
        """Get current time context."""
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
        """Calculate system load from sensor data."""
        flow_readings = [data["value"] for data in sensor_data 
                        if data.get("sensor_type") == "flow"]
        if not flow_readings:
            return 0.5
        
        avg_flow = sum(flow_readings) / len(flow_readings)
        return min(avg_flow / 200.0, 1.0)  # Normalize to 0-1
    
    def _enhanced_planning(self, analysis_result: Any, sensor_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhanced planning using template method approach."""
        
        # Use original planner as base
        original_plan = self.planner_service.select_plans(analysis_result)
        
        # Enhance with pattern-based logic
        enhanced_plan = {
            "base_plan": original_plan,
            "actions": [],
            "strategy": "template_method",
            "timestamp": datetime.now().isoformat()
        }
        
        # Add actions based on analysis
        if isinstance(analysis_result, dict):
            violations = analysis_result.get("violations", [])
            if violations:
                enhanced_plan["actions"].extend([
                    {
                        "type": "adjust_parameter",
                        "parameter": "pressure",
                        "value": 3.5,
                        "reason": "pressure_violation"
                    }
                ])
        
        return enhanced_plan
    
    def _create_command_from_action(self, action: Dict[str, Any]):
        """Create command object from planned action."""
        
        if not PATTERNS_AVAILABLE:
            return None
            
        action_type = action.get("type")
        
        if action_type == "adjust_parameter":
            return SystemParameterAdjustmentCommand(
                parameter_name=action.get("parameter"),
                new_value=action.get("value"),
                target_component=action.get("component", "system")
            )
        
        return None
    
    def _determine_scenario_from_analysis(self, analysis_result: Any):
        """Determine scenario based on analysis results."""
        
        if not PATTERNS_AVAILABLE:
            return "NORMAL"
            
        # Simple scenario determination logic
        if isinstance(analysis_result, dict):
            violations = analysis_result.get("violations", [])
            state = analysis_result.get("state", "NORMAL")
            
            if state == "EMERGENCY" or len(violations) > 3:
                return ScenarioType.EMERGENCY_RESPONSE
            elif len(violations) > 1:
                return ScenarioType.PEAK_DEMAND
        
        return ScenarioType.NORMAL_OPERATION
    
    def _store_enhanced_results(self, sensor_data: List[Dict[str, Any]], 
                              analysis_result: Any, plan_result: Dict[str, Any]):
        """Store enhanced results in database."""
        
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            # Store results for each sensor/node
            for sensor_reading in sensor_data:
                node_id = sensor_reading.get('node_id')
                if node_id:
                    # Store analysis result
                    if isinstance(analysis_result, list):
                        node_analysis = next((result for result in analysis_result 
                                            if result.get('node_id') == node_id), None)
                    else:
                        node_analysis = analysis_result
                    
                    if node_analysis:
                        state = node_analysis.get('state', 'unknown') if isinstance(node_analysis, dict) else 'processed'
                        cur.execute(
                            "INSERT INTO analyze (node_id, result, state) VALUES (%s, %s, %s)",
                            (node_id, str(node_analysis), state)
                        )
                    
                    # Store plan result
                    if plan_result:
                        plan_data = plan_result.get('base_plan', plan_result)
                        if isinstance(plan_data, list):
                            node_plan = next((plan for plan in plan_data 
                                            if plan.get('node_id') == node_id), None)
                        else:
                            node_plan = plan_data
                        
                        if node_plan:
                            priority = node_plan.get('priority') if isinstance(node_plan, dict) else 'normal'
                            cur.execute(
                                "INSERT INTO plan (node_id, result, priority) VALUES (%s, %s, %s)",
                                (node_id, str(node_plan), priority)
                            )
                            cur.execute(
                                "INSERT INTO execute (node_id, result) VALUES (%s, %s)",
                                (node_id, str(node_plan))
                            )
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info("💾 Enhanced results stored in database")
            
        except Exception as e:
            logger.error(f"❌ Database storage failed: {e}")
            if 'conn' in locals():
                try:
                    conn.rollback()
                    cur.close()
                    conn.close()
                except Exception:
                    pass

# Initialize the enhanced system
enhanced_system = EnhancedMAPEKSystem()

def mapek_background_loop():
    """Enhanced MAPE-K background loop with pattern integration."""
    logger.info("[Enhanced MAPE-K] Starting enhanced background loop...")
    
    try:
        # Run the enhanced async loop
        asyncio.run(enhanced_system.enhanced_mapek_loop())
    except Exception as e:
        logger.error(f"[Enhanced MAPE-K] Error in background loop: {e}")

if __name__ == "__main__":
    print("🚀 Enhanced MAPE-K Digital Twin System")
    print("=" * 60)
    
    if PATTERNS_AVAILABLE:
        print("🎯 Advanced Software Engineering Patterns Active:")
        print("   ✅ Strategy Pattern - Scenario-driven analysis")
        print("   ✅ Observer Pattern - Event-driven communication")
        print("   ✅ Command Pattern - Reversible operations")
        print("   ✅ Adapter Pattern - Legacy system integration")
        print("   ✅ Template Method Pattern - Structured pipelines")
    else:
        print("⚠️  Running in basic mode (advanced patterns not available)")
    
    print("=" * 60)
    print("🔄 Starting continuous operation...")
    
    cycle_count = 0
    
    while True:
        cycle_count += 1
        print(f"\n[Cycle {cycle_count}] Running enhanced MAPE-K loop...")
        mapek_background_loop()
        
        if PATTERNS_AVAILABLE:
            total_pattern_usage = sum(enhanced_system.pattern_usage_count.values())
            print(f"📊 Pattern Usage: {total_pattern_usage} total pattern applications")
        
        print(f"⏱️  Waiting 60 seconds before next cycle...\n")
        time.sleep(60)
