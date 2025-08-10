# MAPE-K Water Utility System - API Reference

## Overview

The MAPE-K Water Utility System implements the Monitor-Analyze-Plan-Execute-Knowledge (MAPE-K) architecture pattern for autonomous management of water utility systems. This document provides comprehensive API reference and usage examples.

## Architecture Components

### 1. Monitor Service

The Monitor Service is responsible for collecting sensor data from various water utility sensors.

#### API Reference

```python
from application.services.monitor_service import MonitorService

# Initialize the service
monitor = MonitorService()

# Collect sensor data
sensor_data = await monitor.collect_sensor_data()
```

#### Methods

##### `collect_sensor_data() -> List[SensorData]`

Collects data from all configured sensors.

**Returns:**
- `List[SensorData]`: List of sensor readings

**Raises:**
- `SensorConnectionError`: When sensor connectivity fails
- `ValidationError`: When sensor data validation fails

**Example:**
```python
try:
    data = await monitor.collect_sensor_data()
    for reading in data:
        print(f"Sensor {reading.sensor_id}: {reading.value} {reading.sensor_type}")
except SensorConnectionError as e:
    logger.error(f"Sensor connection failed: {e}")
```

### 2. Analyzer Service

The Analyzer Service processes sensor data to detect threshold violations and assess system state.

#### API Reference

```python
from application.services.analyzer_service import AnalyzerService

# Initialize the service
analyzer = AnalyzerService()

# Analyze sensor data
result = analyzer.analyze(sensor_data)
```

#### Methods

##### `analyze(sensor_data: List[SensorData]) -> Dict[str, Any]`

Analyzes sensor data and determines system state.

**Parameters:**
- `sensor_data`: List of sensor readings to analyze

**Returns:**
- Dictionary containing:
  - `state`: SystemState enum value
  - `violations`: List of detected threshold violations
  - `quality_score`: Float between 0.0 and 1.0
  - `health_status`: SystemHealthStatus enum value

**Example:**
```python
analysis_result = analyzer.analyze(sensor_data)
print(f"System State: {analysis_result['state']}")
print(f"Quality Score: {analysis_result['quality_score']}")
print(f"Violations: {analysis_result['violations']}")
```

#### Threshold Configuration

The analyzer uses configurable thresholds for different sensor types:

| Sensor Type | Normal Range | Warning Threshold | Critical Threshold |
|-------------|--------------|-------------------|-------------------|
| Flow        | 0-100 L/min  | >100 L/min       | >150 L/min       |
| Pressure    | 0-4 bar      | >4 bar           | >5 bar           |
| Quality     | 6-10 pH      | <6 pH            | <4 pH            |
| Temperature | 5-25°C       | >25°C or <5°C    | >35°C or <0°C    |

### 3. Planner Service

The Planner Service creates execution plans based on analysis results.

#### API Reference

```python
from application.services.planner_service import PlannerService

# Initialize the service
planner = PlannerService()

# Create execution plan
plan = planner.create_plan(analysis_result)
```

#### Methods

##### `create_plan(analysis_result: Dict[str, Any]) -> Dict[str, Any]`

Creates an execution plan based on system analysis.

**Parameters:**
- `analysis_result`: Output from analyzer service

**Returns:**
- Dictionary containing:
  - `action`: String describing the action to take
  - `parameters`: Dict of action parameters
  - `priority`: Execution priority (1-5)
  - `estimated_duration`: Expected execution time in seconds

**Example:**
```python
plan = planner.create_plan(analysis_result)
print(f"Planned Action: {plan['action']}")
print(f"Parameters: {plan['parameters']}")
print(f"Priority: {plan['priority']}")
```

#### Available Actions

- `maintain_current_settings`: No action needed, system operating normally
- `reduce_pressure`: Reduce system pressure to safe levels
- `increase_flow`: Increase water flow rate
- `emergency_shutdown`: Immediate system shutdown for critical situations
- `quality_adjustment`: Adjust water treatment parameters

### 4. Executor Service

The Executor Service implements planned actions on the water utility system.

#### API Reference

```python
from application.services.executor_service import ExecutorService

# Initialize the service
executor = ExecutorService()

# Execute plan
result = await executor.execute(plan)
```

#### Methods

##### `execute(plan: Dict[str, Any]) -> Dict[str, Any]`

Executes the specified plan.

**Parameters:**
- `plan`: Execution plan from planner service

**Returns:**
- Dictionary containing:
  - `status`: Execution status ("success", "failed", "partial")
  - `message`: Descriptive message
  - `executed_at`: Timestamp of execution
  - `duration`: Actual execution time

**Example:**
```python
result = await executor.execute(plan)
if result['status'] == 'success':
    print(f"Action executed successfully in {result['duration']}s")
else:
    print(f"Execution failed: {result['message']}")
```

### 5. Knowledge Base

The Knowledge Base stores system state, historical data, and learned patterns.

#### API Reference

```python
from knowledge import KnowledgeBase

# Initialize knowledge base
kb = KnowledgeBase()

# Store system state
await kb.store_state(system_state)

# Retrieve historical data
history = await kb.get_historical_data(time_range)
```

#### Methods

##### `store_state(state: Dict[str, Any]) -> None`

Stores current system state for future reference.

##### `get_historical_data(start_time: str, end_time: str) -> List[Dict[str, Any]]`

Retrieves historical system data for analysis.

##### `update_thresholds(sensor_type: str, thresholds: Dict[str, float]) -> None`

Updates threshold values for adaptive behavior.

## MAPE-K Loop Usage

### Complete Cycle Example

```python
import asyncio
from application.use_cases.mape_loop_use_case import MapeLoopUseCase

async def run_mape_cycle():
    """Execute a complete MAPE-K cycle."""
    mape_loop = MapeLoopUseCase()
    
    try:
        # Execute one complete cycle
        result = await mape_loop.execute_cycle()
        
        print(f"Cycle Status: {result['cycle_status']}")
        print(f"System State: {result['system_state']}")
        
        if result.get('violations_detected'):
            print(f"Violations: {result['violations_detected']}")
        
        return result
        
    except Exception as e:
        logger.error(f"MAPE cycle failed: {e}")
        return {"cycle_status": "failed", "error": str(e)}

# Run the cycle
result = asyncio.run(run_mape_cycle())
```

### Continuous Monitoring

```python
async def continuous_monitoring(interval_seconds=30):
    """Run MAPE-K loop continuously."""
    mape_loop = MapeLoopUseCase()
    
    while True:
        try:
            result = await mape_loop.execute_cycle()
            logger.info(f"Cycle completed: {result['cycle_status']}")
            
            # Wait before next cycle
            await asyncio.sleep(interval_seconds)
            
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"Cycle error: {e}")
            await asyncio.sleep(interval_seconds)

# Start continuous monitoring
asyncio.run(continuous_monitoring())
```

## Data Models

### SensorData

```python
from domain.models import SensorData

sensor_reading = SensorData(
    sensor_id="FLOW_001",
    value=45.2,
    timestamp="2024-01-01T10:00:00Z",
    sensor_type="flow"
)
```

### SystemState Enum

```python
from domain.models import SystemState

# Possible values:
# SystemState.NORMAL - System operating within normal parameters
# SystemState.WARNING - Minor issues detected, monitoring required
# SystemState.CRITICAL - Major issues, immediate action needed
# SystemState.UNKNOWN - Unable to determine system state
```

### ThresholdViolationType Enum

```python
from domain.entities import ThresholdViolationType

# Possible values:
# ThresholdViolationType.HIGH_FLOW
# ThresholdViolationType.LOW_FLOW
# ThresholdViolationType.HIGH_PRESSURE
# ThresholdViolationType.LOW_PRESSURE
# ThresholdViolationType.HIGH_TEMPERATURE
# ThresholdViolationType.LOW_TEMPERATURE
# ThresholdViolationType.POOR_QUALITY
```

## Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/mapek_db
REDIS_URL=redis://localhost:6379/0

# Monitoring Configuration
MONITORING_INTERVAL=30
LOG_LEVEL=INFO

# Sensor Configuration
SENSOR_TIMEOUT=10
MAX_RETRIES=3
```

### Settings File

```python
# config/settings.py
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "mapek_db",
    "user": "mapek_user",
    "password": "secure_password"
}

THRESHOLDS = {
    "flow": {"min": 0, "max": 100, "critical_max": 150},
    "pressure": {"min": 0, "max": 4, "critical_max": 5},
    "quality": {"min": 6, "max": 10, "critical_min": 4},
    "temperature": {"min": 5, "max": 25, "critical_min": 0, "critical_max": 35}
}
```

## Error Handling

### Common Exceptions

```python
from domain.exceptions import (
    SensorConnectionError,
    AnalysisError,
    PlanningError,
    ExecutionError,
    KnowledgeBaseError
)

try:
    result = await mape_loop.execute_cycle()
except SensorConnectionError:
    # Handle sensor connectivity issues
    logger.warning("Sensor connection lost, using cached data")
except AnalysisError as e:
    # Handle analysis failures
    logger.error(f"Analysis failed: {e}")
except ExecutionError as e:
    # Handle execution failures
    logger.error(f"Plan execution failed: {e}")
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def robust_sensor_collection():
    """Sensor collection with automatic retry."""
    return await monitor.collect_sensor_data()
```

## Performance Considerations

### Optimization Tips

1. **Batch Processing**: Process multiple sensor readings together
2. **Caching**: Use Redis for frequently accessed data
3. **Connection Pooling**: Reuse database connections
4. **Async Operations**: Use async/await for I/O operations

### Resource Monitoring

```python
# Monitor system resources
import psutil

def check_system_resources():
    """Check system resource usage."""
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    
    logger.info(f"CPU: {cpu_percent}%, Memory: {memory_percent}%")
    
    if cpu_percent > 80 or memory_percent > 80:
        logger.warning("High resource usage detected")
```

## Security Considerations

### Input Validation

All sensor data is validated using Pydantic models:

```python
from pydantic import BaseModel, validator

class SensorDataInput(BaseModel):
    sensor_id: str
    value: float
    sensor_type: str
    
    @validator('value')
    def validate_value(cls, v):
        if not -1000 <= v <= 1000:
            raise ValueError('Sensor value out of valid range')
        return v
```

### Database Security

- Use parameterized queries to prevent SQL injection
- Implement connection encryption
- Regularly rotate database credentials

### Access Control

```python
from functools import wraps

def require_admin_access(func):
    """Decorator to require admin access for sensitive operations."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check user permissions here
        return await func(*args, **kwargs)
    return wrapper

@require_admin_access
async def update_critical_thresholds(new_thresholds):
    """Update system thresholds (admin only)."""
    pass
```

## Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f mapek-app
```

### Production Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  mapek-app:
    image: mapek-water-utility:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mapek
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=WARNING
    depends_on:
      - db
      - redis
    restart: unless-stopped
```

## Monitoring and Observability

### Health Checks

```python
# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer."""
    health_status = await monitor.health_checker.check_health()
    
    if health_status["healthy"]:
        return {"status": "healthy", "timestamp": time.time()}
    else:
        return {"status": "unhealthy", "details": health_status}, 503
```

### Metrics Collection

```python
# Custom metrics
from infrastructure.monitoring.observability import monitor

# Record custom metrics
monitor.metrics.counter("sensor_readings_total", labels={"sensor_type": "flow"})
monitor.metrics.gauge("water_quality_score", quality_score)
monitor.metrics.histogram("analysis_duration_seconds", analysis_time)
```

## Troubleshooting

### Common Issues

1. **Sensor Connection Failures**
   ```python
   # Check sensor connectivity
   await monitor.test_sensor_connectivity()
   ```

2. **Database Connection Issues**
   ```python
   # Test database connection
   from config.database import test_connection
   await test_connection()
   ```

3. **High Memory Usage**
   ```python
   # Monitor memory usage
   import gc
   gc.collect()  # Force garbage collection
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Enable detailed error tracing
import traceback
try:
    result = await mape_loop.execute_cycle()
except Exception as e:
    traceback.print_exc()
```

## Support and Maintenance

### Log Analysis

```bash
# Search for errors in logs
grep -i error /var/log/mapek/application.log

# Monitor real-time logs
tail -f /var/log/mapek/application.log | grep -i warning
```

### Performance Profiling

```python
import cProfile
import pstats

def profile_mape_cycle():
    """Profile MAPE cycle performance."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run MAPE cycle
    asyncio.run(mape_loop.execute_cycle())
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

For additional support, please refer to the project documentation or contact the development team.
