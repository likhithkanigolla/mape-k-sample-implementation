"""
Comprehensive monitoring and observability configuration for MAPE-K Water Utility System.
Provides metrics collection, alerting, and system health monitoring.
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from contextlib import asynccontextmanager

# Configure structured logging for better observability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """Represents a single metric measurement."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary for serialization."""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp,
            "labels": self.labels
        }


class MetricsCollector:
    """Collects and manages system metrics."""
    
    def __init__(self):
        self.metrics: List[Metric] = []
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
    
    def counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a counter metric."""
        labels = labels or {}
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        self._counters[key] = self._counters.get(key, 0) + value
        
        metric = Metric(name=name, value=self._counters[key], metric_type=MetricType.COUNTER, labels=labels)
        self.metrics.append(metric)
        logger.debug(f"Counter {name} = {self._counters[key]}")
    
    def gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a gauge metric."""
        labels = labels or {}
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        self._gauges[key] = value
        
        metric = Metric(name=name, value=value, metric_type=MetricType.GAUGE, labels=labels)
        self.metrics.append(metric)
        logger.debug(f"Gauge {name} = {value}")
    
    def histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram metric."""
        labels = labels or {}
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        
        metric = Metric(name=name, value=value, metric_type=MetricType.HISTOGRAM, labels=labels)
        self.metrics.append(metric)
        logger.debug(f"Histogram {name} recorded value {value}")
    
    @asynccontextmanager
    async def timer(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.histogram(f"{name}_duration_seconds", duration, labels)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics."""
        return {
            "counters": self._counters,
            "gauges": self._gauges,
            "histograms": {
                k: {
                    "count": len(v),
                    "sum": sum(v),
                    "avg": sum(v) / len(v) if v else 0,
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0
                }
                for k, v in self._histograms.items()
            },
            "total_metrics": len(self.metrics)
        }
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # Export counters
        for key, value in self._counters.items():
            name, labels_str = key.split(':', 1) if ':' in key else (key, '')
            labels_part = f"{{{labels_str}}}" if labels_str else ""
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name}{labels_part} {value}")
        
        # Export gauges
        for key, value in self._gauges.items():
            name, labels_str = key.split(':', 1) if ':' in key else (key, '')
            labels_part = f"{{{labels_str}}}" if labels_str else ""
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name}{labels_part} {value}")
        
        # Export histograms
        for key, values in self._histograms.items():
            name, labels_str = key.split(':', 1) if ':' in key else (key, '')
            labels_part = f"{{{labels_str}}}" if labels_str else ""
            lines.append(f"# TYPE {name} histogram")
            lines.append(f"{name}_count{labels_part} {len(values)}")
            lines.append(f"{name}_sum{labels_part} {sum(values)}")
        
        return '\n'.join(lines) + '\n'


class HealthChecker:
    """Monitors system health and provides health check endpoints."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.health_checks: Dict[str, callable] = {}
        self.last_health_status: Dict[str, bool] = {}
    
    def register_health_check(self, name: str, check_func: callable) -> None:
        """Register a health check function."""
        self.health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform all health checks and return status."""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.health_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    is_healthy = await check_func()
                else:
                    is_healthy = check_func()
                
                results[name] = {
                    "healthy": is_healthy,
                    "timestamp": time.time()
                }
                
                if not is_healthy:
                    overall_healthy = False
                
                # Record metric
                self.metrics.gauge(f"health_check_{name}", 1.0 if is_healthy else 0.0)
                
                # Log if status changed
                if name not in self.last_health_status or self.last_health_status[name] != is_healthy:
                    level = logging.INFO if is_healthy else logging.WARNING
                    logger.log(level, f"Health check '{name}' status changed to: {'healthy' if is_healthy else 'unhealthy'}")
                    self.last_health_status[name] = is_healthy
                    
            except Exception as e:
                logger.error(f"Health check '{name}' failed with exception: {e}")
                results[name] = {
                    "healthy": False,
                    "error": str(e),
                    "timestamp": time.time()
                }
                overall_healthy = False
                self.metrics.gauge(f"health_check_{name}", 0.0)
        
        # Record overall health
        self.metrics.gauge("system_health_overall", 1.0 if overall_healthy else 0.0)
        
        return {
            "healthy": overall_healthy,
            "checks": results,
            "timestamp": time.time()
        }


class AlertManager:
    """Manages alerts based on system metrics and health status."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alert_rules: List[Dict[str, Any]] = []
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
    
    def add_alert_rule(self, name: str, condition: callable, severity: str = "warning", 
                      description: str = "") -> None:
        """Add an alert rule."""
        rule = {
            "name": name,
            "condition": condition,
            "severity": severity,
            "description": description
        }
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {name}")
    
    async def evaluate_alerts(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate all alert rules and return active alerts."""
        new_alerts = []
        
        for rule in self.alert_rules:
            try:
                if asyncio.iscoroutinefunction(rule["condition"]):
                    is_firing = await rule["condition"](context)
                else:
                    is_firing = rule["condition"](context)
                
                alert_key = rule["name"]
                
                if is_firing:
                    if alert_key not in self.active_alerts:
                        # New alert
                        alert = {
                            "name": rule["name"],
                            "severity": rule["severity"],
                            "description": rule["description"],
                            "started_at": time.time(),
                            "status": "firing"
                        }
                        self.active_alerts[alert_key] = alert
                        new_alerts.append(alert)
                        
                        logger.warning(f"Alert FIRING: {rule['name']} - {rule['description']}")
                        self.metrics.counter("alerts_fired_total", labels={"alert": rule["name"]})
                else:
                    if alert_key in self.active_alerts:
                        # Alert resolved
                        resolved_alert = self.active_alerts.pop(alert_key)
                        resolved_alert["status"] = "resolved"
                        resolved_alert["resolved_at"] = time.time()
                        resolved_alert["duration"] = resolved_alert["resolved_at"] - resolved_alert["started_at"]
                        
                        logger.info(f"Alert RESOLVED: {rule['name']} after {resolved_alert['duration']:.2f} seconds")
                        self.metrics.counter("alerts_resolved_total", labels={"alert": rule["name"]})
                        
            except Exception as e:
                logger.error(f"Error evaluating alert rule '{rule['name']}': {e}")
        
        return new_alerts
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all currently active alerts."""
        return list(self.active_alerts.values())


class MapeKMonitor:
    """Main monitoring class that coordinates all observability components."""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.health_checker = HealthChecker(self.metrics)
        self.alert_manager = AlertManager(self.metrics)
        self.monitoring_active = False
        self._setup_default_health_checks()
        self._setup_default_alerts()
    
    def _setup_default_health_checks(self):
        """Set up default health checks for MAPE-K components."""
        
        def database_health():
            # Simplified database health check
            # In real implementation, would check actual database connectivity
            return True
        
        def redis_health():
            # Simplified Redis health check
            # In real implementation, would check actual Redis connectivity
            return True
        
        def memory_health():
            # Check memory usage
            import psutil
            memory_percent = psutil.virtual_memory().percent
            return memory_percent < 90  # Alert if memory usage > 90%
        
        self.health_checker.register_health_check("database", database_health)
        self.health_checker.register_health_check("redis", redis_health)
        self.health_checker.register_health_check("memory", memory_health)
    
    def _setup_default_alerts(self):
        """Set up default alert rules."""
        
        def high_error_rate(context):
            error_count = context.get("error_count", 0)
            total_count = context.get("total_count", 1)
            error_rate = error_count / total_count
            return error_rate > 0.05  # Alert if error rate > 5%
        
        def low_quality_score(context):
            quality_score = context.get("quality_score", 1.0)
            return quality_score < 0.7  # Alert if quality score < 0.7
        
        def high_violation_count(context):
            violation_count = context.get("violation_count", 0)
            return violation_count > 5  # Alert if more than 5 violations
        
        self.alert_manager.add_alert_rule(
            "high_error_rate",
            high_error_rate,
            "critical",
            "MAPE-K system error rate is above 5%"
        )
        
        self.alert_manager.add_alert_rule(
            "low_quality_score", 
            low_quality_score,
            "warning",
            "System quality score has dropped below 0.7"
        )
        
        self.alert_manager.add_alert_rule(
            "high_violation_count",
            high_violation_count,
            "warning", 
            "High number of threshold violations detected"
        )
    
    async def start_monitoring(self, interval: int = 30):
        """Start the monitoring loop."""
        self.monitoring_active = True
        logger.info("Starting MAPE-K monitoring")
        
        while self.monitoring_active:
            try:
                # Perform health checks
                health_status = await self.health_checker.check_health()
                
                # Create context for alert evaluation
                alert_context = {
                    "health_status": health_status,
                    "error_count": 0,  # Would be populated from actual metrics
                    "total_count": 100,  # Would be populated from actual metrics
                    "quality_score": 0.8,  # Would be populated from actual analysis
                    "violation_count": 2   # Would be populated from actual analysis
                }
                
                # Evaluate alerts
                new_alerts = await self.alert_manager.evaluate_alerts(alert_context)
                
                # Log monitoring summary
                metrics_summary = self.metrics.get_metrics_summary()
                active_alerts = self.alert_manager.get_active_alerts()
                
                logger.info(f"Monitoring cycle completed - "
                          f"Health: {'OK' if health_status['healthy'] else 'DEGRADED'}, "
                          f"Metrics: {metrics_summary['total_metrics']}, "
                          f"Active alerts: {len(active_alerts)}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop the monitoring loop."""
        self.monitoring_active = False
        logger.info("Stopping MAPE-K monitoring")
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        return {
            "metrics": self.metrics.get_metrics_summary(),
            "health": self.health_checker.last_health_status,
            "alerts": {
                "active": self.alert_manager.get_active_alerts(),
                "total_rules": len(self.alert_manager.alert_rules)
            },
            "timestamp": time.time()
        }


# Global monitor instance
monitor = MapeKMonitor()


# Decorator for monitoring function execution
def monitor_execution(operation_name: str):
    """Decorator to monitor function execution time and errors."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            async with monitor.metrics.timer(f"{operation_name}_execution"):
                try:
                    result = await func(*args, **kwargs)
                    monitor.metrics.counter(f"{operation_name}_success_total")
                    return result
                except Exception as e:
                    monitor.metrics.counter(f"{operation_name}_error_total", labels={"error_type": type(e).__name__})
                    logger.error(f"Error in {operation_name}: {e}")
                    raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                monitor.metrics.histogram(f"{operation_name}_execution_duration_seconds", duration)
                monitor.metrics.counter(f"{operation_name}_success_total")
                return result
            except Exception as e:
                duration = time.time() - start_time
                monitor.metrics.histogram(f"{operation_name}_execution_duration_seconds", duration)
                monitor.metrics.counter(f"{operation_name}_error_total", labels={"error_type": type(e).__name__})
                logger.error(f"Error in {operation_name}: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
