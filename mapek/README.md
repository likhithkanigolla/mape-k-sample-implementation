# Advanced Software Engineering Patterns for Digital Twin Water Utility Networks

## 🎯 Research Objective

This implementation demonstrates **advanced software engineering patterns, architectural patterns, and design patterns** for developing **scenario-driven digital twins in water utility networks**. This work supports research in "Leveraging Software Engineering Practices for Developing Scenario-Driven Digital Twins in Water Utility Networks."

## 🏗️ Architecture Overview

### Core MAPE-K Components
```
├── Monitor    # Sensor data collection and monitoring
├── Analyze    # Threshold analysis and state detection
├── Plan      # Decision making and action planning
├── Execute   # Action implementation and control
└── Knowledge # Learning and adaptation
```

### Advanced Pattern Integration
```
├── Strategy Pattern      # Scenario-driven analysis adaptation
├── Observer Pattern      # Event-driven communication
├── Command Pattern       # Reversible operations
├── Adapter Pattern       # Legacy system integration
└── Template Method       # Consistent pipeline execution
```

## 🎨 Implemented Design Patterns

### 1. Strategy Pattern - Scenario-Driven Analysis
**Location**: `domain/strategies/scenario_analysis_strategy.py`

**Research Contribution**: Enables dynamic behavioral adaptation based on operational scenarios.

```python
class ScenarioAnalyzer:
    def __init__(self):
        self.strategies = {
            ScenarioType.NORMAL_OPERATION: NormalOperationStrategy(),
            ScenarioType.PEAK_DEMAND: PeakDemandStrategy(),
            ScenarioType.EMERGENCY_RESPONSE: EmergencyResponseStrategy(),
            ScenarioType.DROUGHT_CONDITIONS: DroughtConditionsStrategy(),
        }
```

**Key Features**:
- ✅ Context-aware threshold adaptation
- ✅ Time-of-day and weather consideration
- ✅ Load-factor based analysis
- ✅ Extensible scenario framework

**Academic Significance**: Demonstrates how behavioral patterns enable **adaptive digital twins** that respond to **real-world operational contexts**.

### 2. Observer Pattern - Event-Driven Communication
**Location**: `domain/events/event_system.py`

**Research Contribution**: Enables real-time, loosely-coupled communication across digital twin components.

```python
class DigitalTwinEventBus(EventSubject):
    async def notify(self, event: Event) -> None:
        observers = self._observers.get(event.event_type, [])
        tasks = [asyncio.create_task(observer.on_event(event)) for observer in observers]
        await asyncio.gather(*tasks, return_exceptions=True)
```

**Key Features**:
- ✅ Asynchronous event processing
- ✅ Event filtering and transformation
- ✅ Performance metrics and monitoring
- ✅ Event correlation support

**Academic Significance**: Shows how **event-driven architectures** support **real-time responsiveness** critical for infrastructure management.
- **Executor**: Executes plans with async HTTP requests, circuit breaker, and retry logic.
- **Config**: All settings are environment-driven and centralized.
- **Logging & Metrics**: Structured logs and Prometheus metrics for observability.
- **Caching**: Redis used for threshold caching to improve performance.
- **Testing**: Unit tests for core business logic.

## How to Run
1. **Install dependencies**:
   - Python 3.11+
   - `pip install -r requirements.txt`
   # - Install Redis server for caching (optional, recommended for production)
   # - Install Prometheus for metrics scraping (optional, recommended for production)
2. **Configure environment variables** (see `config/settings.py`)
3. **Start the main loop**:
   - Run the async loop in `application/use_cases/mape_loop_use_case.py`
   - Example:
     ```bash
     python -m mapek.application.use_cases.mape_loop_use_case
     ```
4. **Run tests**:
   - `pytest mapek/tests/unit/`

## Notes
- All legacy files (`analyze.py`, `execute.py`, `plan.py`, `monitor.py`, etc.) are superseded by this modular implementation.
- For production, ensure all required Python packages are installed (see errors for missing packages).
- Extend services and repositories for additional business logic as needed.

## Authors
- Implementation: GitHub Copilot
- Architecture: Based on best practices for MAPE-K and industrial IoT systems
