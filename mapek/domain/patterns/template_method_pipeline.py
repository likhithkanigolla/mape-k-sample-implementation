"""
Template Method Pattern Implementation for MAPE-K Pipeline
Defines the skeleton of the MAPE-K algorithm while allowing subclasses to override specific steps.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import asyncio
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Stages in the MAPE-K pipeline."""
    MONITOR = "monitor"
    ANALYZE = "analyze"
    PLAN = "plan"
    EXECUTE = "execute"
    KNOWLEDGE_UPDATE = "knowledge_update"


class PipelineResult(Enum):
    """Results of pipeline execution."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    ABORTED = "aborted"


@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage."""
    stage: PipelineStage
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    data_size: int = 0
    processing_rate: float = 0.0


@dataclass
class PipelineContext:
    """Context object passed through the pipeline stages."""
    pipeline_id: str
    start_time: datetime
    current_stage: PipelineStage
    sensor_data: List[Dict[str, Any]]
    analysis_result: Dict[str, Any]
    execution_plan: Dict[str, Any]
    execution_result: Dict[str, Any]
    knowledge_updates: Dict[str, Any]
    metadata: Dict[str, Any]
    stage_metrics: List[StageMetrics]
    
    def add_metric(self, metric: StageMetrics) -> None:
        """Add a stage metric to the context."""
        self.stage_metrics.append(metric)
    
    def get_total_duration(self) -> float:
        """Get total pipeline duration in milliseconds."""
        return sum(metric.duration_ms for metric in self.stage_metrics)
    
    def get_stage_metric(self, stage: PipelineStage) -> Optional[StageMetrics]:
        """Get metric for a specific stage."""
        return next((m for m in self.stage_metrics if m.stage == stage), None)


class MapeKPipelineTemplate(ABC):
    """Template method pattern for MAPE-K pipeline execution."""
    
    def __init__(self, pipeline_name: str, config: Optional[Dict[str, Any]] = None):
        self.pipeline_name = pipeline_name
        self.config = config or {}
        self.hooks_enabled = self.config.get("enable_hooks", True)
        self.error_handling_strategy = self.config.get("error_strategy", "continue")
        self.performance_monitoring = self.config.get("monitor_performance", True)
        
    async def execute_pipeline(self, initial_data: Dict[str, Any]) -> PipelineContext:
        """
        Template method that defines the structure of the MAPE-K pipeline.
        This is the main algorithm that cannot be overridden.
        """
        # Initialize pipeline context
        context = PipelineContext(
            pipeline_id=f"{self.pipeline_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_time=datetime.now(),
            current_stage=PipelineStage.MONITOR,
            sensor_data=[],
            analysis_result={},
            execution_plan={},
            execution_result={},
            knowledge_updates={},
            metadata=initial_data.copy(),
            stage_metrics=[]
        )
        
        logger.info(f"Starting MAPE-K pipeline: {context.pipeline_id}")
        
        try:
            # Pre-execution hook
            if self.hooks_enabled:
                await self.pre_execution_hook(context)
            
            # MONITOR phase
            await self._execute_stage(context, PipelineStage.MONITOR, self.monitor_phase)
            
            # ANALYZE phase
            await self._execute_stage(context, PipelineStage.ANALYZE, self.analyze_phase)
            
            # PLAN phase
            await self._execute_stage(context, PipelineStage.PLAN, self.plan_phase)
            
            # EXECUTE phase
            await self._execute_stage(context, PipelineStage.EXECUTE, self.execute_phase)
            
            # KNOWLEDGE UPDATE phase
            await self._execute_stage(context, PipelineStage.KNOWLEDGE_UPDATE, self.update_knowledge_phase)
            
            # Post-execution hook
            if self.hooks_enabled:
                await self.post_execution_hook(context)
            
            logger.info(f"MAPE-K pipeline completed: {context.pipeline_id} "
                       f"(Total time: {context.get_total_duration():.2f}ms)")
            
            return context
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            if self.hooks_enabled:
                await self.error_hook(context, e)
            raise
    
    async def _execute_stage(self, context: PipelineContext, stage: PipelineStage, 
                           stage_func) -> None:
        """Execute a single pipeline stage with error handling and metrics."""
        context.current_stage = stage
        start_time = datetime.now()
        
        try:
            logger.debug(f"Executing stage: {stage.value}")
            
            # Execute the stage
            await stage_func(context)
            
            # Calculate metrics
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            if self.performance_monitoring:
                data_size = self._calculate_data_size(context, stage)
                processing_rate = data_size / max(duration, 1.0) if data_size > 0 else 0.0
                
                metric = StageMetrics(
                    stage=stage,
                    duration_ms=duration,
                    success=True,
                    data_size=data_size,
                    processing_rate=processing_rate
                )
                context.add_metric(metric)
            
            logger.debug(f"Stage {stage.value} completed in {duration:.2f}ms")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            # Record failure metric
            if self.performance_monitoring:
                metric = StageMetrics(
                    stage=stage,
                    duration_ms=duration,
                    success=False,
                    error_message=str(e)
                )
                context.add_metric(metric)
            
            logger.error(f"Stage {stage.value} failed after {duration:.2f}ms: {e}")
            
            # Handle error based on strategy
            if self.error_handling_strategy == "abort":
                raise
            elif self.error_handling_strategy == "continue":
                logger.warning(f"Continuing pipeline despite {stage.value} failure")
            elif self.error_handling_strategy == "retry":
                await self._retry_stage(context, stage, stage_func)
    
    async def _retry_stage(self, context: PipelineContext, stage: PipelineStage, 
                          stage_func, max_retries: int = 3) -> None:
        """Retry a failed stage with exponential backoff."""
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying stage {stage.value}, attempt {attempt + 1}")
                await stage_func(context)
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Stage {stage.value} failed after {max_retries} attempts")
                    raise
                logger.warning(f"Retry {attempt + 1} for stage {stage.value} failed: {e}")
    
    def _calculate_data_size(self, context: PipelineContext, stage: PipelineStage) -> int:
        """Calculate data size for performance metrics."""
        if stage == PipelineStage.MONITOR:
            return len(context.sensor_data)
        elif stage == PipelineStage.ANALYZE:
            return len(str(context.analysis_result))
        elif stage == PipelineStage.PLAN:
            return len(str(context.execution_plan))
        elif stage == PipelineStage.EXECUTE:
            return len(str(context.execution_result))
        else:
            return 0
    
    # Abstract methods that subclasses must implement
    @abstractmethod
    async def monitor_phase(self, context: PipelineContext) -> None:
        """Monitor phase: collect sensor data and system state."""
        pass
    
    @abstractmethod
    async def analyze_phase(self, context: PipelineContext) -> None:
        """Analyze phase: process sensor data and detect issues."""
        pass
    
    @abstractmethod
    async def plan_phase(self, context: PipelineContext) -> None:
        """Plan phase: create execution plan based on analysis."""
        pass
    
    @abstractmethod
    async def execute_phase(self, context: PipelineContext) -> None:
        """Execute phase: implement the planned actions."""
        pass
    
    @abstractmethod
    async def update_knowledge_phase(self, context: PipelineContext) -> None:
        """Knowledge update phase: update system knowledge base."""
        pass
    
    # Hook methods that subclasses can override
    async def pre_execution_hook(self, context: PipelineContext) -> None:
        """Hook called before pipeline execution starts."""
        logger.debug(f"Pre-execution hook for pipeline: {context.pipeline_id}")
    
    async def post_execution_hook(self, context: PipelineContext) -> None:
        """Hook called after successful pipeline execution."""
        logger.debug(f"Post-execution hook for pipeline: {context.pipeline_id}")
    
    async def error_hook(self, context: PipelineContext, error: Exception) -> None:
        """Hook called when pipeline execution fails."""
        logger.error(f"Error hook for pipeline {context.pipeline_id}: {error}")


class StandardWaterUtilityPipeline(MapeKPipelineTemplate):
    """Standard implementation of MAPE-K pipeline for water utility systems."""
    
    def __init__(self, sensor_service, analyzer_service, planner_service, 
                 executor_service, knowledge_service):
        super().__init__("StandardWaterUtility")
        self.sensor_service = sensor_service
        self.analyzer_service = analyzer_service
        self.planner_service = planner_service
        self.executor_service = executor_service
        self.knowledge_service = knowledge_service
    
    async def monitor_phase(self, context: PipelineContext) -> None:
        """Collect sensor data from water utility systems."""
        logger.debug("Executing monitor phase - collecting sensor data")
        
        # Collect sensor data
        sensor_data = await self.sensor_service.collect_sensor_data()
        context.sensor_data = [data.dict() if hasattr(data, 'dict') else data for data in sensor_data]
        
        # Add monitoring metadata
        context.metadata.update({
            "sensors_count": len(context.sensor_data),
            "monitor_timestamp": datetime.now().isoformat(),
            "data_quality": self._assess_data_quality(context.sensor_data)
        })
        
        logger.info(f"Monitored {len(context.sensor_data)} sensors")
    
    async def analyze_phase(self, context: PipelineContext) -> None:
        """Analyze sensor data for threshold violations and system state."""
        logger.debug("Executing analyze phase - processing sensor data")
        
        if not context.sensor_data:
            logger.warning("No sensor data available for analysis")
            context.analysis_result = {"state": "UNKNOWN", "violations": [], "quality_score": 0.0}
            return
        
        # Convert sensor data back to appropriate format for analyzer
        sensor_objects = []
        for data in context.sensor_data:
            # Create sensor objects from data
            sensor_objects.append(data)
        
        # Perform analysis
        analysis_result = self.analyzer_service.analyze(sensor_objects)
        context.analysis_result = analysis_result
        
        # Add analysis metadata
        context.metadata.update({
            "analysis_timestamp": datetime.now().isoformat(),
            "violations_count": len(analysis_result.get("violations", [])),
            "system_state": analysis_result.get("state"),
            "quality_score": analysis_result.get("quality_score", 0.0)
        })
        
        logger.info(f"Analysis completed - State: {analysis_result.get('state')}, "
                   f"Quality: {analysis_result.get('quality_score', 0.0):.2f}")
    
    async def plan_phase(self, context: PipelineContext) -> None:
        """Create execution plan based on analysis results."""
        logger.debug("Executing plan phase - creating action plan")
        
        if not context.analysis_result:
            logger.warning("No analysis result available for planning")
            context.execution_plan = {"action": "no_action", "reason": "no_analysis_data"}
            return
        
        # Create execution plan
        plan = self.planner_service.create_plan(context.analysis_result)
        context.execution_plan = plan
        
        # Add planning metadata
        context.metadata.update({
            "plan_timestamp": datetime.now().isoformat(),
            "planned_action": plan.get("action"),
            "plan_priority": plan.get("priority", 1),
            "estimated_duration": plan.get("estimated_duration", 0)
        })
        
        logger.info(f"Plan created - Action: {plan.get('action')}, "
                   f"Priority: {plan.get('priority', 1)}")
    
    async def execute_phase(self, context: PipelineContext) -> None:
        """Execute the planned actions on the water utility system."""
        logger.debug("Executing execute phase - implementing actions")
        
        if not context.execution_plan or context.execution_plan.get("action") == "no_action":
            logger.info("No action required - skipping execution")
            context.execution_result = {"status": "skipped", "reason": "no_action_needed"}
            return
        
        # Execute the plan
        execution_result = await self.executor_service.execute(context.execution_plan)
        context.execution_result = execution_result
        
        # Add execution metadata
        context.metadata.update({
            "execution_timestamp": datetime.now().isoformat(),
            "execution_status": execution_result.get("status"),
            "execution_duration": execution_result.get("duration", 0)
        })
        
        logger.info(f"Execution completed - Status: {execution_result.get('status')}")
    
    async def update_knowledge_phase(self, context: PipelineContext) -> None:
        """Update knowledge base with new observations and results."""
        logger.debug("Executing knowledge update phase")
        
        # Prepare knowledge updates
        knowledge_data = {
            "sensor_readings": context.sensor_data,
            "analysis_result": context.analysis_result,
            "execution_plan": context.execution_plan,
            "execution_result": context.execution_result,
            "pipeline_metrics": [m.__dict__ for m in context.stage_metrics],
            "timestamp": datetime.now().isoformat()
        }
        
        # Update knowledge base
        await self.knowledge_service.store_pipeline_execution(knowledge_data)
        
        # Extract patterns and update system parameters if needed
        patterns = await self.knowledge_service.analyze_patterns(context.sensor_data)
        if patterns:
            context.knowledge_updates = patterns
            logger.info(f"Knowledge updated with {len(patterns)} new patterns")
        
        context.metadata["knowledge_update_timestamp"] = datetime.now().isoformat()
    
    def _assess_data_quality(self, sensor_data: List[Dict[str, Any]]) -> str:
        """Assess the quality of collected sensor data."""
        if not sensor_data:
            return "no_data"
        
        valid_readings = sum(1 for data in sensor_data 
                           if data.get("value") is not None and 
                           isinstance(data.get("value"), (int, float)))
        
        quality_ratio = valid_readings / len(sensor_data)
        
        if quality_ratio >= 0.95:
            return "excellent"
        elif quality_ratio >= 0.8:
            return "good"
        elif quality_ratio >= 0.6:
            return "fair"
        else:
            return "poor"


class EmergencyResponsePipeline(MapeKPipelineTemplate):
    """Emergency response pipeline with enhanced monitoring and rapid execution."""
    
    def __init__(self, emergency_services, alert_service):
        config = {
            "enable_hooks": True,
            "error_strategy": "abort",  # Strict error handling for emergencies
            "monitor_performance": True
        }
        super().__init__("EmergencyResponse", config)
        self.emergency_services = emergency_services
        self.alert_service = alert_service
        self.emergency_thresholds = {
            "pressure": {"critical_high": 5.0, "critical_low": 1.0},
            "flow": {"critical_high": 200.0, "critical_low": 5.0},
            "quality": {"critical_low": 4.0}
        }
    
    async def monitor_phase(self, context: PipelineContext) -> None:
        """Enhanced monitoring for emergency situations."""
        logger.warning("Emergency monitoring phase - increased sampling rate")
        
        # Collect data with higher frequency and redundancy
        sensor_data = []
        for attempt in range(3):  # Triple redundancy for emergency
            try:
                data = await self.emergency_services.collect_critical_sensors()
                sensor_data.extend(data)
                break
            except Exception as e:
                logger.error(f"Emergency monitoring attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    raise
        
        context.sensor_data = sensor_data
        context.metadata.update({
            "emergency_mode": True,
            "redundant_sampling": True,
            "sensors_count": len(sensor_data)
        })
    
    async def analyze_phase(self, context: PipelineContext) -> None:
        """Critical analysis with emergency thresholds."""
        logger.warning("Emergency analysis phase - applying critical thresholds")
        
        analysis_result = {"state": "UNKNOWN", "violations": [], "critical_violations": []}
        
        for sensor_data in context.sensor_data:
            sensor_type = sensor_data.get("sensor_type")
            value = sensor_data.get("value")
            
            if sensor_type in self.emergency_thresholds and value is not None:
                thresholds = self.emergency_thresholds[sensor_type]
                
                if "critical_high" in thresholds and value > thresholds["critical_high"]:
                    analysis_result["critical_violations"].append({
                        "sensor": sensor_data.get("sensor_id"),
                        "type": f"CRITICAL_HIGH_{sensor_type.upper()}",
                        "value": value,
                        "threshold": thresholds["critical_high"]
                    })
                
                if "critical_low" in thresholds and value < thresholds["critical_low"]:
                    analysis_result["critical_violations"].append({
                        "sensor": sensor_data.get("sensor_id"),
                        "type": f"CRITICAL_LOW_{sensor_type.upper()}",
                        "value": value,
                        "threshold": thresholds["critical_low"]
                    })
        
        # Determine emergency state
        if analysis_result["critical_violations"]:
            analysis_result["state"] = "EMERGENCY_CRITICAL"
            analysis_result["quality_score"] = 0.0
        else:
            analysis_result["state"] = "EMERGENCY_MONITORING"
            analysis_result["quality_score"] = 0.5
        
        context.analysis_result = analysis_result
        
        # Trigger immediate alerts for critical violations
        if analysis_result["critical_violations"]:
            await self.alert_service.trigger_emergency_alert(analysis_result["critical_violations"])
    
    async def plan_phase(self, context: PipelineContext) -> None:
        """Emergency planning with predefined response protocols."""
        logger.warning("Emergency planning phase - activating response protocols")
        
        critical_violations = context.analysis_result.get("critical_violations", [])
        
        if not critical_violations:
            context.execution_plan = {"action": "continue_monitoring", "priority": 5}
            return
        
        # Create emergency response plan
        emergency_actions = []
        
        for violation in critical_violations:
            if "PRESSURE" in violation["type"]:
                if "HIGH" in violation["type"]:
                    emergency_actions.append({
                        "action": "emergency_pressure_relief",
                        "target": "main_relief_valve",
                        "parameters": {"immediate": True}
                    })
                else:
                    emergency_actions.append({
                        "action": "emergency_pump_activation",
                        "target": "backup_pump_system",
                        "parameters": {"immediate": True}
                    })
            
            elif "FLOW" in violation["type"]:
                emergency_actions.append({
                    "action": "emergency_flow_isolation",
                    "target": "affected_zone",
                    "parameters": {"zone_id": violation["sensor"], "immediate": True}
                })
            
            elif "QUALITY" in violation["type"]:
                emergency_actions.append({
                    "action": "emergency_water_isolation",
                    "target": "contaminated_section",
                    "parameters": {"immediate": True, "notify_authorities": True}
                })
        
        context.execution_plan = {
            "action": "emergency_response",
            "emergency_actions": emergency_actions,
            "priority": 5,  # Maximum priority
            "estimated_duration": 30,  # 30 seconds for emergency response
            "requires_confirmation": False  # Auto-execute in emergency
        }
    
    async def execute_phase(self, context: PipelineContext) -> None:
        """Immediate execution of emergency response actions."""
        logger.critical("Emergency execution phase - implementing immediate response")
        
        plan = context.execution_plan
        if plan.get("action") != "emergency_response":
            context.execution_result = {"status": "no_emergency_action"}
            return
        
        execution_results = []
        
        # Execute all emergency actions in parallel for speed
        emergency_actions = plan.get("emergency_actions", [])
        tasks = []
        
        for action in emergency_actions:
            task = asyncio.create_task(
                self.emergency_services.execute_emergency_action(action)
            )
            tasks.append(task)
        
        # Wait for all emergency actions to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                execution_results.append({
                    "action": emergency_actions[i]["action"],
                    "status": "failed",
                    "error": str(result)
                })
            else:
                execution_results.append(result)
        
        context.execution_result = {
            "status": "emergency_executed",
            "actions_completed": len([r for r in execution_results if r.get("status") == "success"]),
            "actions_failed": len([r for r in execution_results if r.get("status") == "failed"]),
            "detailed_results": execution_results
        }
    
    async def update_knowledge_phase(self, context: PipelineContext) -> None:
        """Update emergency response knowledge and incident records."""
        logger.info("Emergency knowledge update - recording incident details")
        
        incident_record = {
            "incident_id": context.pipeline_id,
            "incident_type": "emergency_response",
            "critical_violations": context.analysis_result.get("critical_violations", []),
            "response_actions": context.execution_plan.get("emergency_actions", []),
            "response_effectiveness": context.execution_result,
            "total_response_time": context.get_total_duration(),
            "timestamp": context.start_time.isoformat()
        }
        
        # Store incident for analysis and improvement
        await self.emergency_services.record_emergency_incident(incident_record)
        
        context.knowledge_updates = {
            "incident_recorded": True,
            "incident_id": context.pipeline_id,
            "response_time_ms": context.get_total_duration()
        }
    
    async def pre_execution_hook(self, context: PipelineContext) -> None:
        """Emergency pre-execution hook - notify stakeholders."""
        logger.critical(f"EMERGENCY PIPELINE ACTIVATED: {context.pipeline_id}")
        await self.alert_service.notify_emergency_start(context.pipeline_id)
    
    async def post_execution_hook(self, context: PipelineContext) -> None:
        """Emergency post-execution hook - status update."""
        total_time = context.get_total_duration()
        logger.critical(f"EMERGENCY PIPELINE COMPLETED: {context.pipeline_id} "
                       f"(Response time: {total_time:.2f}ms)")
        
        await self.alert_service.notify_emergency_completion(
            context.pipeline_id, 
            total_time, 
            context.execution_result
        )


class OptimizationPipeline(MapeKPipelineTemplate):
    """Pipeline focused on system optimization and efficiency improvements."""
    
    def __init__(self, optimization_service, ml_service):
        config = {
            "enable_hooks": True,
            "error_strategy": "continue",
            "monitor_performance": True
        }
        super().__init__("Optimization", config)
        self.optimization_service = optimization_service
        self.ml_service = ml_service
        self.optimization_targets = ["energy_efficiency", "water_quality", "flow_optimization"]
    
    async def monitor_phase(self, context: PipelineContext) -> None:
        """Monitor with focus on optimization metrics."""
        # Collect both current data and historical trends
        current_data = await self.optimization_service.collect_current_metrics()
        historical_data = await self.optimization_service.get_historical_trends(
            hours=24  # Last 24 hours for trend analysis
        )
        
        context.sensor_data = current_data
        context.metadata.update({
            "historical_data": historical_data,
            "optimization_mode": True,
            "data_collection_timestamp": datetime.now().isoformat()
        })
    
    async def analyze_phase(self, context: PipelineContext) -> None:
        """Advanced analysis with ML-based optimization recommendations."""
        # Standard threshold analysis
        basic_analysis = await self.optimization_service.basic_analysis(context.sensor_data)
        
        # ML-based optimization analysis
        ml_recommendations = await self.ml_service.generate_optimization_recommendations(
            current_data=context.sensor_data,
            historical_data=context.metadata.get("historical_data", []),
            targets=self.optimization_targets
        )
        
        context.analysis_result = {
            **basic_analysis,
            "optimization_opportunities": ml_recommendations,
            "efficiency_score": await self._calculate_efficiency_score(context),
            "analysis_type": "optimization"
        }
    
    async def plan_phase(self, context: PipelineContext) -> None:
        """Create optimization plan based on ML recommendations."""
        recommendations = context.analysis_result.get("optimization_opportunities", [])
        
        if not recommendations:
            context.execution_plan = {"action": "maintain_current_settings"}
            return
        
        # Prioritize recommendations by impact and feasibility
        prioritized_actions = sorted(
            recommendations,
            key=lambda x: (x.get("impact_score", 0) * x.get("feasibility_score", 0)),
            reverse=True
        )
        
        # Select top actions that can be executed safely
        selected_actions = []
        for action in prioritized_actions[:3]:  # Top 3 actions
            if action.get("safety_score", 0) > 0.8:  # Only safe actions
                selected_actions.append(action)
        
        context.execution_plan = {
            "action": "optimization_sequence",
            "optimization_actions": selected_actions,
            "priority": 2,  # Medium priority
            "estimated_duration": sum(a.get("duration", 60) for a in selected_actions),
            "expected_improvement": sum(a.get("impact_score", 0) for a in selected_actions)
        }
    
    async def execute_phase(self, context: PipelineContext) -> None:
        """Execute optimization actions with monitoring."""
        plan = context.execution_plan
        
        if plan.get("action") != "optimization_sequence":
            context.execution_result = {"status": "no_optimization_needed"}
            return
        
        optimization_results = []
        baseline_metrics = await self.optimization_service.capture_baseline_metrics()
        
        for action in plan.get("optimization_actions", []):
            result = await self.optimization_service.execute_optimization_action(action)
            
            # Monitor immediate impact
            post_action_metrics = await self.optimization_service.capture_current_metrics()
            impact_assessment = await self.optimization_service.assess_action_impact(
                baseline_metrics, post_action_metrics, action
            )
            
            result["impact_assessment"] = impact_assessment
            optimization_results.append(result)
            
            # Brief pause between actions to allow system stabilization
            await asyncio.sleep(30)
        
        context.execution_result = {
            "status": "optimization_completed",
            "actions_executed": len(optimization_results),
            "detailed_results": optimization_results,
            "overall_improvement": await self._calculate_overall_improvement(optimization_results)
        }
    
    async def update_knowledge_phase(self, context: PipelineContext) -> None:
        """Update ML models and optimization knowledge."""
        # Record optimization session
        optimization_session = {
            "session_id": context.pipeline_id,
            "baseline_metrics": context.metadata.get("baseline_metrics"),
            "actions_taken": context.execution_plan.get("optimization_actions", []),
            "results_achieved": context.execution_result.get("detailed_results", []),
            "overall_improvement": context.execution_result.get("overall_improvement", 0),
            "timestamp": context.start_time.isoformat()
        }
        
        # Update ML models with new data
        await self.ml_service.update_optimization_models(optimization_session)
        
        # Update system parameters if improvements were significant
        overall_improvement = context.execution_result.get("overall_improvement", 0)
        if overall_improvement > 0.05:  # 5% improvement threshold
            await self.optimization_service.update_system_parameters(context.execution_result)
        
        context.knowledge_updates = {
            "ml_models_updated": True,
            "optimization_session_recorded": True,
            "improvement_achieved": overall_improvement
        }
    
    async def _calculate_efficiency_score(self, context: PipelineContext) -> float:
        """Calculate current system efficiency score."""
        # Simplified efficiency calculation
        # In practice, this would involve complex metrics
        return 0.85  # Placeholder
    
    async def _calculate_overall_improvement(self, optimization_results: List[Dict[str, Any]]) -> float:
        """Calculate overall improvement from optimization actions."""
        improvements = [r.get("impact_assessment", {}).get("improvement", 0) 
                       for r in optimization_results]
        return sum(improvements) / len(improvements) if improvements else 0.0


# Pipeline factory for creating different pipeline types
class PipelineFactory:
    """Factory for creating different types of MAPE-K pipelines."""
    
    @staticmethod
    def create_standard_pipeline(services) -> StandardWaterUtilityPipeline:
        """Create standard water utility pipeline."""
        return StandardWaterUtilityPipeline(
            sensor_service=services["sensor"],
            analyzer_service=services["analyzer"],
            planner_service=services["planner"],
            executor_service=services["executor"],
            knowledge_service=services["knowledge"]
        )
    
    @staticmethod
    def create_emergency_pipeline(emergency_services, alert_service) -> EmergencyResponsePipeline:
        """Create emergency response pipeline."""
        return EmergencyResponsePipeline(emergency_services, alert_service)
    
    @staticmethod
    def create_optimization_pipeline(optimization_service, ml_service) -> OptimizationPipeline:
        """Create optimization-focused pipeline."""
        return OptimizationPipeline(optimization_service, ml_service)


# Pipeline orchestrator for managing multiple pipeline types
class PipelineOrchestrator:
    """Orchestrates multiple MAPE-K pipelines for different scenarios."""
    
    def __init__(self):
        self.pipelines: Dict[str, MapeKPipelineTemplate] = {}
        self.active_executions: Dict[str, PipelineContext] = {}
        self.execution_history: List[PipelineContext] = []
    
    def register_pipeline(self, name: str, pipeline: MapeKPipelineTemplate) -> None:
        """Register a pipeline with the orchestrator."""
        self.pipelines[name] = pipeline
        logger.info(f"Registered pipeline: {name}")
    
    async def execute_pipeline(self, pipeline_name: str, 
                             initial_data: Dict[str, Any]) -> PipelineContext:
        """Execute a specific pipeline."""
        if pipeline_name not in self.pipelines:
            raise ValueError(f"Pipeline '{pipeline_name}' not registered")
        
        pipeline = self.pipelines[pipeline_name]
        context = await pipeline.execute_pipeline(initial_data)
        
        # Track execution
        self.active_executions[context.pipeline_id] = context
        self.execution_history.append(context)
        
        # Clean up active executions
        del self.active_executions[context.pipeline_id]
        
        return context
    
    async def execute_parallel_pipelines(self, pipeline_configs: List[Tuple[str, Dict[str, Any]]]) -> List[PipelineContext]:
        """Execute multiple pipelines in parallel."""
        tasks = []
        
        for pipeline_name, initial_data in pipeline_configs:
            task = asyncio.create_task(self.execute_pipeline(pipeline_name, initial_data))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        successful_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Pipeline execution failed: {result}")
            else:
                successful_results.append(result)
        
        return successful_results
    
    def get_pipeline_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of all executed pipelines."""
        if not self.execution_history:
            return {"message": "No pipeline executions recorded"}
        
        summary = {
            "total_executions": len(self.execution_history),
            "pipelines": {}
        }
        
        # Group by pipeline type
        for context in self.execution_history:
            pipeline_type = context.pipeline_id.split('_')[0]
            
            if pipeline_type not in summary["pipelines"]:
                summary["pipelines"][pipeline_type] = {
                    "executions": 0,
                    "total_duration_ms": 0,
                    "average_duration_ms": 0,
                    "success_rate": 0
                }
            
            pipeline_stats = summary["pipelines"][pipeline_type]
            pipeline_stats["executions"] += 1
            pipeline_stats["total_duration_ms"] += context.get_total_duration()
            
            # Calculate success rate based on stage metrics
            successful_stages = sum(1 for m in context.stage_metrics if m.success)
            total_stages = len(context.stage_metrics)
            stage_success_rate = successful_stages / total_stages if total_stages > 0 else 0
            
            pipeline_stats["success_rate"] = (
                (pipeline_stats["success_rate"] * (pipeline_stats["executions"] - 1) + stage_success_rate) /
                pipeline_stats["executions"]
            )
        
        # Calculate average durations
        for pipeline_type, stats in summary["pipelines"].items():
            if stats["executions"] > 0:
                stats["average_duration_ms"] = stats["total_duration_ms"] / stats["executions"]
        
        return summary
