"""
Observer Pattern Implementation for Event-Driven Digital Twin Communication
Enables real-time event propagation across the MAPE-K system components.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
import json
from uuid import uuid4

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events in the digital twin system."""
    # Sensor Events
    SENSOR_DATA_RECEIVED = "sensor_data_received"
    SENSOR_OFFLINE = "sensor_offline"
    SENSOR_ONLINE = "sensor_online"
    SENSOR_ANOMALY = "sensor_anomaly"
    
    # Analysis Events
    THRESHOLD_VIOLATION = "threshold_violation"
    SYSTEM_STATE_CHANGE = "system_state_change"
    QUALITY_DEGRADATION = "quality_degradation"
    ANALYSIS_COMPLETED = "analysis_completed"
    
    # Planning Events
    PLAN_CREATED = "plan_created"
    PLAN_UPDATED = "plan_updated"
    EMERGENCY_PLAN_TRIGGERED = "emergency_plan_triggered"
    
    # Execution Events
    ACTION_STARTED = "action_started"
    ACTION_COMPLETED = "action_completed"
    ACTION_FAILED = "action_failed"
    SYSTEM_ADJUSTMENT_MADE = "system_adjustment_made"
    
    # Knowledge Events
    KNOWLEDGE_UPDATED = "knowledge_updated"
    PATTERN_DETECTED = "pattern_detected"
    THRESHOLD_ADAPTED = "threshold_adapted"
    
    # System Events
    MAPE_CYCLE_STARTED = "mape_cycle_started"
    MAPE_CYCLE_COMPLETED = "mape_cycle_completed"
    SYSTEM_HEALTH_CHANGED = "system_health_changed"
    ALERT_TRIGGERED = "alert_triggered"


@dataclass
class Event:
    """Represents an event in the digital twin system."""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: EventType = EventType.SENSOR_DATA_RECEIVED
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=critical
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data,
            "priority": self.priority,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(
            event_id=data.get("event_id", str(uuid4())),
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data.get("source", "unknown"),
            data=data.get("data", {}),
            priority=data.get("priority", 1),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {})
        )


class EventObserver(ABC):
    """Abstract base class for event observers."""
    
    @abstractmethod
    async def on_event(self, event: Event) -> None:
        """Handle an event notification."""
        pass
    
    @abstractmethod
    def get_interested_events(self) -> Set[EventType]:
        """Return set of event types this observer is interested in."""
        pass
    
    def get_observer_id(self) -> str:
        """Return unique identifier for this observer."""
        return f"{self.__class__.__name__}_{id(self)}"


class EventSubject(ABC):
    """Abstract base class for event subjects (publishers)."""
    
    def __init__(self):
        self._observers: Dict[EventType, List[EventObserver]] = {}
        self._event_history: List[Event] = []
        self._max_history_size = 1000
    
    def subscribe(self, observer: EventObserver) -> None:
        """Subscribe an observer to relevant events."""
        interested_events = observer.get_interested_events()
        
        for event_type in interested_events:
            if event_type not in self._observers:
                self._observers[event_type] = []
            
            if observer not in self._observers[event_type]:
                self._observers[event_type].append(observer)
                logger.info(f"Observer {observer.get_observer_id()} subscribed to {event_type.value}")
    
    def unsubscribe(self, observer: EventObserver) -> None:
        """Unsubscribe an observer from all events."""
        for event_type, observers in self._observers.items():
            if observer in observers:
                observers.remove(observer)
                logger.info(f"Observer {observer.get_observer_id()} unsubscribed from {event_type.value}")
    
    async def notify(self, event: Event) -> None:
        """Notify all interested observers about an event."""
        # Add to event history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)
        
        # Get observers for this event type
        observers = self._observers.get(event.event_type, [])
        
        if observers:
            logger.debug(f"Notifying {len(observers)} observers about {event.event_type.value}")
            
            # Notify all observers concurrently
            tasks = []
            for observer in observers:
                try:
                    task = asyncio.create_task(observer.on_event(event))
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Error creating task for observer {observer.get_observer_id()}: {e}")
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_event_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """Get recent event history."""
        if event_type:
            filtered_events = [e for e in self._event_history if e.event_type == event_type]
            return filtered_events[-limit:]
        return self._event_history[-limit:]
    
    def get_observer_count(self, event_type: EventType) -> int:
        """Get number of observers for an event type."""
        return len(self._observers.get(event_type, []))


class DigitalTwinEventBus(EventSubject):
    """Central event bus for the digital twin system."""
    
    def __init__(self):
        super().__init__()
        self._event_filters: List[Callable[[Event], bool]] = []
        self._event_transformers: List[Callable[[Event], Event]] = []
        self._metrics = {
            "events_published": 0,
            "events_filtered": 0,
            "observer_notifications": 0,
            "notification_errors": 0
        }
    
    def add_event_filter(self, filter_func: Callable[[Event], bool]) -> None:
        """Add a filter function that determines if an event should be processed."""
        self._event_filters.append(filter_func)
    
    def add_event_transformer(self, transformer_func: Callable[[Event], Event]) -> None:
        """Add a transformer function that modifies events before publishing."""
        self._event_transformers.append(transformer_func)
    
    async def publish(self, event: Event) -> bool:
        """Publish an event to all interested observers."""
        self._metrics["events_published"] += 1
        
        # Apply filters
        for filter_func in self._event_filters:
            try:
                if not filter_func(event):
                    self._metrics["events_filtered"] += 1
                    logger.debug(f"Event {event.event_id} filtered out")
                    return False
            except Exception as e:
                logger.error(f"Error in event filter: {e}")
        
        # Apply transformers
        for transformer_func in self._event_transformers:
            try:
                event = transformer_func(event)
            except Exception as e:
                logger.error(f"Error in event transformer: {e}")
        
        # Notify observers
        try:
            await self.notify(event)
            self._metrics["observer_notifications"] += 1
            logger.debug(f"Event {event.event_id} published successfully")
            return True
        except Exception as e:
            self._metrics["notification_errors"] += 1
            logger.error(f"Error publishing event {event.event_id}: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, int]:
        """Get event bus metrics."""
        return self._metrics.copy()
    
    def clear_metrics(self) -> None:
        """Clear event bus metrics."""
        self._metrics = {key: 0 for key in self._metrics}


# Concrete Observer Implementations

class SensorDataObserver(EventObserver):
    """Observer for sensor-related events."""
    
    def __init__(self, sensor_id: Optional[str] = None):
        self.sensor_id = sensor_id
        self.sensor_data_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 100
    
    async def on_event(self, event: Event) -> None:
        """Handle sensor events."""
        if event.event_type == EventType.SENSOR_DATA_RECEIVED:
            # Filter by sensor ID if specified
            if self.sensor_id and event.data.get("sensor_id") != self.sensor_id:
                return
            
            # Buffer sensor data for analysis
            self.sensor_data_buffer.append(event.data)
            if len(self.sensor_data_buffer) > self.max_buffer_size:
                self.sensor_data_buffer.pop(0)
            
            logger.debug(f"Buffered sensor data from {event.data.get('sensor_id')}")
            
        elif event.event_type == EventType.SENSOR_OFFLINE:
            logger.warning(f"Sensor {event.data.get('sensor_id')} went offline")
            
        elif event.event_type == EventType.SENSOR_ANOMALY:
            logger.alert(f"Anomaly detected in sensor {event.data.get('sensor_id')}: {event.data.get('anomaly_type')}")
    
    def get_interested_events(self) -> Set[EventType]:
        """Return sensor-related events."""
        return {
            EventType.SENSOR_DATA_RECEIVED,
            EventType.SENSOR_OFFLINE,
            EventType.SENSOR_ONLINE,
            EventType.SENSOR_ANOMALY
        }
    
    def get_buffered_data(self) -> List[Dict[str, Any]]:
        """Get buffered sensor data."""
        return self.sensor_data_buffer.copy()


class SystemStateObserver(EventObserver):
    """Observer for system state changes."""
    
    def __init__(self):
        self.state_history: List[Dict[str, Any]] = []
        self.current_state = "UNKNOWN"
        self.state_change_count = 0
    
    async def on_event(self, event: Event) -> None:
        """Handle system state events."""
        if event.event_type == EventType.SYSTEM_STATE_CHANGE:
            old_state = self.current_state
            new_state = event.data.get("new_state", "UNKNOWN")
            
            self.current_state = new_state
            self.state_change_count += 1
            
            self.state_history.append({
                "timestamp": event.timestamp.isoformat(),
                "old_state": old_state,
                "new_state": new_state,
                "change_reason": event.data.get("reason", "unknown")
            })
            
            logger.info(f"System state changed from {old_state} to {new_state}")
            
        elif event.event_type == EventType.THRESHOLD_VIOLATION:
            logger.warning(f"Threshold violation detected: {event.data}")
            
        elif event.event_type == EventType.QUALITY_DEGRADATION:
            logger.warning(f"Quality degradation detected: {event.data}")
    
    def get_interested_events(self) -> Set[EventType]:
        """Return system state related events."""
        return {
            EventType.SYSTEM_STATE_CHANGE,
            EventType.THRESHOLD_VIOLATION,
            EventType.QUALITY_DEGRADATION,
            EventType.SYSTEM_HEALTH_CHANGED
        }
    
    def get_state_history(self) -> List[Dict[str, Any]]:
        """Get system state change history."""
        return self.state_history.copy()


class ActionObserver(EventObserver):
    """Observer for action execution events."""
    
    def __init__(self):
        self.active_actions: Dict[str, Dict[str, Any]] = {}
        self.completed_actions: List[Dict[str, Any]] = []
        self.failed_actions: List[Dict[str, Any]] = []
    
    async def on_event(self, event: Event) -> None:
        """Handle action events."""
        if event.event_type == EventType.ACTION_STARTED:
            action_id = event.data.get("action_id", event.event_id)
            self.active_actions[action_id] = {
                "action_type": event.data.get("action_type"),
                "start_time": event.timestamp.isoformat(),
                "parameters": event.data.get("parameters", {}),
                "status": "running"
            }
            logger.info(f"Action {action_id} started: {event.data.get('action_type')}")
            
        elif event.event_type == EventType.ACTION_COMPLETED:
            action_id = event.data.get("action_id", event.event_id)
            if action_id in self.active_actions:
                action_info = self.active_actions.pop(action_id)
                action_info.update({
                    "end_time": event.timestamp.isoformat(),
                    "status": "completed",
                    "result": event.data.get("result", {})
                })
                self.completed_actions.append(action_info)
                logger.info(f"Action {action_id} completed successfully")
            
        elif event.event_type == EventType.ACTION_FAILED:
            action_id = event.data.get("action_id", event.event_id)
            if action_id in self.active_actions:
                action_info = self.active_actions.pop(action_id)
                action_info.update({
                    "end_time": event.timestamp.isoformat(),
                    "status": "failed",
                    "error": event.data.get("error", "unknown error")
                })
                self.failed_actions.append(action_info)
                logger.error(f"Action {action_id} failed: {event.data.get('error')}")
    
    def get_interested_events(self) -> Set[EventType]:
        """Return action-related events."""
        return {
            EventType.ACTION_STARTED,
            EventType.ACTION_COMPLETED,
            EventType.ACTION_FAILED,
            EventType.SYSTEM_ADJUSTMENT_MADE
        }
    
    def get_action_summary(self) -> Dict[str, Any]:
        """Get summary of action execution."""
        return {
            "active_actions": len(self.active_actions),
            "completed_actions": len(self.completed_actions),
            "failed_actions": len(self.failed_actions),
            "success_rate": len(self.completed_actions) / max(1, len(self.completed_actions) + len(self.failed_actions))
        }


class AlertObserver(EventObserver):
    """Observer for alert and notification events."""
    
    def __init__(self, alert_callback: Optional[Callable] = None):
        self.alert_callback = alert_callback
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_history: List[Dict[str, Any]] = []
    
    async def on_event(self, event: Event) -> None:
        """Handle alert events."""
        if event.event_type == EventType.ALERT_TRIGGERED:
            alert_id = event.data.get("alert_id", event.event_id)
            alert_info = {
                "alert_id": alert_id,
                "severity": event.data.get("severity", "medium"),
                "message": event.data.get("message", "Unknown alert"),
                "timestamp": event.timestamp.isoformat(),
                "source": event.source,
                "data": event.data
            }
            
            self.active_alerts[alert_id] = alert_info
            self.alert_history.append(alert_info)
            
            logger.warning(f"Alert triggered: {alert_info['message']}")
            
            # Call external alert callback if provided
            if self.alert_callback:
                try:
                    await self.alert_callback(alert_info)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
        
        elif event.event_type in [EventType.THRESHOLD_VIOLATION, EventType.EMERGENCY_PLAN_TRIGGERED]:
            # Automatically create alerts for critical events
            auto_alert = Event(
                event_type=EventType.ALERT_TRIGGERED,
                source=event.source,
                data={
                    "alert_id": f"auto_{event.event_id}",
                    "severity": "high" if event.event_type == EventType.EMERGENCY_PLAN_TRIGGERED else "medium",
                    "message": f"Automatic alert for {event.event_type.value}",
                    "original_event": event.to_dict()
                },
                priority=3 if event.event_type == EventType.EMERGENCY_PLAN_TRIGGERED else 2
            )
            await self.on_event(auto_alert)
    
    def get_interested_events(self) -> Set[EventType]:
        """Return alert-related events."""
        return {
            EventType.ALERT_TRIGGERED,
            EventType.THRESHOLD_VIOLATION,
            EventType.EMERGENCY_PLAN_TRIGGERED,
            EventType.SYSTEM_HEALTH_CHANGED
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts."""
        return list(self.active_alerts.values())
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge and remove an active alert."""
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]
            logger.info(f"Alert {alert_id} acknowledged")
            return True
        return False


# Event Factory and Utilities

class EventFactory:
    """Factory for creating standardized events."""
    
    @staticmethod
    def create_sensor_event(sensor_id: str, sensor_data: Dict[str, Any], 
                          event_type: EventType = EventType.SENSOR_DATA_RECEIVED) -> Event:
        """Create a sensor-related event."""
        return Event(
            event_type=event_type,
            source=f"sensor_{sensor_id}",
            data={
                "sensor_id": sensor_id,
                "sensor_data": sensor_data,
                "reading_time": sensor_data.get("timestamp")
            },
            priority=1
        )
    
    @staticmethod
    def create_state_change_event(old_state: str, new_state: str, reason: str) -> Event:
        """Create a system state change event."""
        return Event(
            event_type=EventType.SYSTEM_STATE_CHANGE,
            source="analyzer",
            data={
                "old_state": old_state,
                "new_state": new_state,
                "reason": reason
            },
            priority=2
        )
    
    @staticmethod
    def create_action_event(action_type: str, action_id: str, 
                          event_type: EventType, **kwargs) -> Event:
        """Create an action-related event."""
        return Event(
            event_type=event_type,
            source="executor",
            data={
                "action_type": action_type,
                "action_id": action_id,
                **kwargs
            },
            priority=2
        )
    
    @staticmethod
    def create_alert_event(severity: str, message: str, alert_data: Dict[str, Any]) -> Event:
        """Create an alert event."""
        return Event(
            event_type=EventType.ALERT_TRIGGERED,
            source="alert_system",
            data={
                "severity": severity,
                "message": message,
                **alert_data
            },
            priority=3 if severity == "high" else 2
        )


# Global event bus instance
global_event_bus = DigitalTwinEventBus()


# Decorator for automatic event publishing
def publish_event(event_type: EventType, source: str = "unknown"):
    """Decorator to automatically publish events for function calls."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Create start event
            start_event = Event(
                event_type=event_type,
                source=source,
                data={
                    "function": func.__name__,
                    "status": "started",
                    "args": str(args)[:100],  # Truncate for logging
                    "kwargs": str(kwargs)[:100]
                }
            )
            await global_event_bus.publish(start_event)
            
            try:
                result = await func(*args, **kwargs)
                
                # Create completion event
                completion_event = Event(
                    event_type=event_type,
                    source=source,
                    data={
                        "function": func.__name__,
                        "status": "completed",
                        "result_summary": str(result)[:100] if result else "None"
                    },
                    correlation_id=start_event.event_id
                )
                await global_event_bus.publish(completion_event)
                
                return result
                
            except Exception as e:
                # Create error event
                error_event = Event(
                    event_type=EventType.ACTION_FAILED,
                    source=source,
                    data={
                        "function": func.__name__,
                        "status": "failed",
                        "error": str(e)
                    },
                    correlation_id=start_event.event_id,
                    priority=3
                )
                await global_event_bus.publish(error_event)
                raise
        
        def sync_wrapper(*args, **kwargs):
            # For sync functions, create a simple completion event
            try:
                result = func(*args, **kwargs)
                event = Event(
                    event_type=event_type,
                    source=source,
                    data={
                        "function": func.__name__,
                        "status": "completed"
                    }
                )
                # Note: sync functions can't publish events directly
                # This is mainly for demonstration
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
