# MAPE-K Water Utility Implementation (Production-Ready)

## Overview
This project implements a robust, modular, and production-ready MAPE-K architecture for water utility IoT systems. It features:
- **Database connection pooling** (psycopg2)
- **Centralized configuration management**
- **Repository pattern** for data access
- **Dependency injection container**
- **Async/await main loop** for scalability
- **Circuit breaker and retry logic** for node communication
- **Pydantic input validation** in both monitor and analyze
- **Data quality pipeline** (outlier, freshness, etc.)
- **Redis caching layer** for thresholds
- **Structured logging and Prometheus metrics**
- **Comprehensive unit test scaffolding**

## Directory Structure
```
mapek/
├── config/
│   ├── settings.py
│   └── database.py
├── domain/
│   ├── models.py
│   └── entities.py
├── infrastructure/
│   ├── database/
│   │   ├── repositories.py
│   │   └── cached_threshold_repository.py
│   └── cache/
│       └── redis_client.py
├── application/
│   ├── services/
│   │   ├── container.py
│   │   ├── monitor_service.py
│   │   ├── analyzer_service.py
│   │   ├── planner_service.py
│   │   └── executor_service.py
│   └── use_cases/
│       └── mape_loop_use_case.py
├── logger.py
├── tests/
│   └── unit/
│       └── test_analyzer.py
```

## Key Features
- **Monitor**: Validates and sanitizes raw sensor data using Pydantic models.
- **Analyzer**: Applies business logic, threshold checks, and data quality assessment.
- **Planner**: Selects plans based on analysis results using repository pattern.
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
