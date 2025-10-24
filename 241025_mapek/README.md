# Plain MAPE-K Implementation (Without Design Patterns)

This folder contains a **simple, straightforward implementation** of the MAPE-K (Monitor-Analyze-Plan-Execute-Knowledge) loop for a Digital Twin water utility system, **without advanced software engineering patterns**.

## 📁 Folder Structure

```
241025_mapek/
├── plain_mapek/          # Plain MAPE-K implementation
│   ├── main.py          # Main MAPE-K loop
│   ├── monitor.py       # Monitor component
│   ├── analyze.py       # Analyze component
│   ├── plan.py          # Plan component
│   ├── execute.py       # Execute component
│   ├── knowledge.py     # Database utilities
│   └── logger.py        # Logging configuration
│
├── iot_scripts/         # IoT sensor simulators
│   ├── water_quality_sensor.py
│   ├── water_flow_sensor.py
│   ├── water_level_sensor.py
│   └── motor_sensor.py
│
└── logs/                # Log files (created automatically)
```

## 🎯 What is MAPE-K?

MAPE-K is a control loop architecture for autonomic/self-managing systems:

- **Monitor**: Collect sensor data from IoT devices
- **Analyze**: Compare data against thresholds
- **Plan**: Select appropriate action plans based on analysis
- **Execute**: Execute the selected plans
- **Knowledge**: Shared database with system state and configuration

## 🔄 Comparison: Plain vs Pattern-Based Implementation

### This Implementation (Plain MAPE-K)
- ✅ **Simple and Direct**: Easy to understand and modify
- ✅ **Minimal Dependencies**: Just basic Python libraries
- ✅ **Straightforward Logic**: No abstraction layers
- ✅ **Good for Learning**: Clear MAPE-K concept demonstration
- ⚠️ **Limited Flexibility**: Harder to extend with new features
- ⚠️ **Less Scalable**: Not optimized for large systems

### Pattern-Based Implementation (`/mapek`)
- ✅ **Advanced Patterns**: Strategy, Observer, Command, Adapter, Template Method
- ✅ **Highly Flexible**: Easy to add new scenarios and behaviors
- ✅ **Scalable**: Designed for complex systems
- ✅ **Production Ready**: Robust error handling and extensibility
- ⚠️ **More Complex**: Requires understanding of design patterns
- ⚠️ **More Code**: Higher initial complexity

## 🚀 Quick Start

### Prerequisites

1. **PostgreSQL Database** running on `localhost:5432`
   - Database: `mapek_dt`
   - User: `postgres`
   - Password: `postgres`

2. **Python 3.8+** with required packages:
   ```bash
   pip install psycopg2-binary requests
   ```

3. **FastAPI Server** (from `/app`) running on port 3043:
   ```bash
   cd app
   uvicorn main:app --host 0.0.0.0 --port 3043
   ```

### Database Setup

Ensure your database has the required tables:
- `water_quality`, `water_flow`, `water_level`, `motor` (sensor data)
- `thresholds` (parameter thresholds)
- `plans` (action plans)
- `nodes` (IoT node information)
- `analyze`, `plan_selection`, `execution` (MAPE-K results)

### Running the System

#### Step 1: Start IoT Sensors

Open 4 terminal windows and run each sensor:

```bash
# Terminal 1: Water Quality Sensor
cd 241025_mapek/iot_scripts
python water_quality_sensor.py

# Terminal 2: Water Flow Sensor
python water_flow_sensor.py

# Terminal 3: Water Level Sensor
python water_level_sensor.py

# Terminal 4: Motor Sensor
python motor_sensor.py
```

The sensors will continuously post data to the API every 60 seconds, with 30% chance of anomalies.

#### Step 2: Start MAPE-K Loop

In a new terminal:

```bash
cd 241025_mapek/plain_mapek
python main.py
```

The MAPE-K loop will:
1. Read sensor data from database (Monitor)
2. Analyze data against thresholds (Analyze)
3. Select appropriate plans (Plan)
4. Execute plans (Execute)
5. Wait 60 seconds and repeat

## 📊 How It Works

### Monitor Phase
```python
# Reads latest sensor data from database
sensor_data = monitor.read_sensors()
# Returns: [{'node_id': 'water_quality_1', 'temperature': 25.3, ...}, ...]
```

### Analyze Phase
```python
# Compares each parameter against thresholds
analysis_results = analyzer.analyze(sensor_data)
# Returns: [{'node_id': 'water_quality_1', 'state': 'normal', ...}, ...]
# States: 'normal', 'warning', 'critical'
```

### Plan Phase
```python
# Selects action plans based on system state
selected_plans = planner.select_plans(analysis_results)
# Returns: [{'node_id': 'water_quality_1', 'plan': {...}}, ...]
```

### Execute Phase
```python
# Executes the selected plans (simulated for now)
execution_results = executor.execute(selected_plans)
# Returns: [{'node_id': 'water_quality_1', 'status': 'success', ...}, ...]
```

## 🔍 Monitoring and Logs

### Console Output
The system logs to both console and file, showing:
- Each MAPE-K cycle number
- Sensor readings
- Analysis results (violations and states)
- Selected plans
- Execution results

### Log Files
Check `241025_mapek/logs/plain_mapek.log` for detailed logs.

### Database Records
Query the database to see historical data:
```sql
-- View analysis results
SELECT * FROM analyze ORDER BY timestamp DESC LIMIT 10;

-- View plan selections
SELECT * FROM plan_selection ORDER BY timestamp DESC LIMIT 10;

-- View execution results
SELECT * FROM execution ORDER BY timestamp DESC LIMIT 10;
```

## 🛠️ Customization

### Adjust MAPE-K Cycle Interval
Edit `main.py`:
```python
mapek.run(interval=30)  # Run every 30 seconds instead of 60
```

### Adjust Sensor Posting Frequency
Edit sensor scripts (e.g., `water_quality_sensor.py`):
```python
time.sleep(30)  # Post every 30 seconds instead of 60
```

### Adjust Anomaly Probability
Edit sensor scripts:
```python
if random.random() < 0.5:  # 50% anomaly rate instead of 30%
```

## 📈 Expected Behavior

### Normal Operation
- All sensors report values within thresholds
- Analysis shows 'normal' state
- Plans for 'normal' state are selected
- Execution succeeds

### Warning State
- Some parameters exceed thresholds
- Analysis shows 'warning' state
- Plans for 'warning' state are selected (e.g., "increase monitoring frequency")

### Critical State
- Many parameters exceed thresholds
- Analysis shows 'critical' state
- Plans for 'critical' state are selected (e.g., "shutdown system", "alert operators")

## 🐛 Troubleshooting

### "Database connection error"
- Check PostgreSQL is running: `pg_isready`
- Verify database exists: `psql -U postgres -d mapek_dt`
- Check credentials in `knowledge.py`

### "Error sending data" (from sensors)
- Ensure FastAPI server is running on port 3043
- Check server logs for errors
- Verify API endpoints match sensor URLs

### "No sensor data available"
- Wait 60 seconds for sensors to post first data
- Check database tables have recent data
- Verify sensors are running

## 📚 Next Steps

### For Learning
1. Study each MAPE-K component file
2. Add print statements to trace execution flow
3. Modify threshold values in database and observe behavior
4. Create new sensor types

### For Development
1. Compare with pattern-based implementation in `/mapek`
2. Implement actual IoT device communication (replace simulation)
3. Add more sophisticated analysis algorithms
4. Implement real plan execution (not simulated)

## 🔗 Related Files

- **Pattern-Based Implementation**: `/mapek` - Advanced version with design patterns
- **FastAPI Server**: `/app/main.py` - API server for receiving sensor data
- **Database Schema**: `/mapek/create_tables.sql` - Database setup

## 📝 Notes

- This is a **simplified educational implementation**
- Execution is currently **simulated** (no actual IoT commands sent)
- For production use, see the pattern-based implementation in `/mapek`
- Database connections are created per operation (not pooled)
- Error handling is basic (suitable for learning, not production)

## 🤝 Contributing

This is a learning implementation. Feel free to:
- Add more sensor types
- Improve error handling
- Add unit tests
- Create visualization tools
- Document edge cases

---

**Created**: October 24, 2025  
**Purpose**: Educational plain MAPE-K implementation for Digital Twin systems  
**Maintainer**: IIITH Code Files - Digital Twin Project
