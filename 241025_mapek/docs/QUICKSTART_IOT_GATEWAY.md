# IoT Gateway System - Quick Start Guide

## What Was Created

You now have a **complete bidirectional IoT system** with:

1. **Central IoT Gateway** (`iot_gateway.py`) - FastAPI server on port 3043
2. **4 IoT Sensor Scripts** - Each with data sender + command receiver
3. **Updated MAPE-K Execute** - Sends commands through Gateway
4. **Startup/Shutdown Scripts** - Easy management
5. **Complete Documentation** - See `IOT_GATEWAY_README.md`

## Quick Start (3 Steps)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database
```bash
# Run in PostgreSQL
psql -U postgres -d iot_mapek -f setup_execution_log.sql
```

### 3. Start Everything
```bash
# Make scripts executable (first time only)
chmod +x start_iot_gateway.sh stop_iot_gateway.sh

# Start Gateway and all sensors
./start_iot_gateway.sh

# In another terminal, start MAPE-K
cd plain_mapek
python3 main.py
```

## How It Works

### Data Flow (Monitoring)
```
IoT Sensors → POST data → Gateway → PostgreSQL ← MAPE-K Monitor reads
```

### Command Flow (Execution)
```
MAPE-K Execute → Gateway → Routes to Device → Device applies fix
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│ IoT Sensors (4 devices with command receivers) │
│   • water_quality_1:8001                        │
│   • water_level_1:8002                          │
│   • water_flow_1:8003                           │
│   • motor_1:8004                                │
└────────────────┬────────────────────────────────┘
                 │
                 ↓ Send data every 60s
┌─────────────────────────────────────────────────┐
│        IoT Gateway :3043 (FastAPI)              │
│  ┌──────────────────────────────────────┐      │
│  │ • Receives sensor data               │      │
│  │ • Stores in PostgreSQL               │      │
│  │ • Provides Monitor endpoints         │      │
│  │ • Routes Execute commands to devices │      │
│  └──────────────────────────────────────┘      │
└────────────────┬────────────────────────────────┘
                 │
                 ↓ Monitor reads / Execute sends
┌─────────────────────────────────────────────────┐
│           MAPE-K Control Loop                   │
│  Monitor → Analyze → Plan → Execute             │
└─────────────────────────────────────────────────┘
```

## Realistic Behavior

### 1. Sensors Generate Anomalies (30% chance)
```
[Cycle 1] Normal: {temperature: 25.4, tds_voltage: 1.2, ...}
[Cycle 2] ANOMALY: {temperature: 52.3, tds_voltage: 4.1, ...}
[Cycle 3] ANOMALY: {temperature: 48.7, tds_voltage: 3.9, ...}
```

### 2. MAPE-K Detects and Plans
```
Analyze: Detected HIGH_TDS_VOLTAGE on water_quality_1
Plan: Selected RECALIBRATE_SENSOR
```

### 3. Execute Sends Command via Gateway
```
Execute → POST /execute/command
{
  "node_id": "water_quality_1",
  "plan_code": "RECALIBRATE_SENSOR",
  "description": "Recalibrate water quality sensor"
}
```

### 4. Gateway Routes to Device
```
Gateway: Forwarding to http://localhost:8001/command
Device: ✓ Command received - Applying fix
```

### 5. Device Self-Heals
```
[Cycle 4] FIXED - Normal operation restored: {temperature: 24.1, ...}
[Cycle 5] FIXED - Normal operation restored: {temperature: 26.3, ...}
[Cycle 6] FIXED - Normal operation restored: {temperature: 25.8, ...}
[Cycle 7] Normal: {temperature: 27.2, ...}  ← Back to normal
```

## Key Features

### ✅ Realistic IoT Architecture
- Central Gateway for all communication
- Device registry for dynamic routing
- Proper error handling and timeouts

### ✅ Bidirectional Communication
- Sensors → Gateway: Data ingestion
- MAPE-K → Gateway: Monitor queries
- MAPE-K → Gateway → Devices: Command execution

### ✅ Self-Healing Behavior
- Devices detect anomalies
- MAPE-K sends fix commands
- Devices apply fixes and recover
- System returns to normal operation

### ✅ Complete Observability
- Gateway logs all data and commands
- Sensors log their state changes
- MAPE-K logs execution results
- Database tracks execution history

## File Structure

```
241025_mapek/
├── iot_gateway.py              # Central FastAPI gateway
├── start_iot_gateway.sh        # Start all services
├── stop_iot_gateway.sh         # Stop all services
├── setup_execution_log.sql     # Database setup
├── requirements.txt            # Python dependencies
├── IOT_GATEWAY_README.md       # Full documentation
├── iot_scripts/
│   ├── water_quality_sensor.py # Port 8001
│   ├── water_level_sensor.py   # Port 8002
│   ├── water_flow_sensor.py    # Port 8003
│   └── motor_sensor.py         # Port 8004
└── plain_mapek/
    ├── execute.py              # Updated to use Gateway
    ├── monitor.py
    ├── analyze.py
    ├── plan.py
    └── main.py
```

## Testing

### 1. Check Gateway Health
```bash
curl http://localhost:3043/
```

### 2. View Registered Devices
```bash
curl http://localhost:3043/devices
```

### 3. Get Latest Sensor Data
```bash
curl http://localhost:3043/monitor/water_quality/latest?limit=3
```

### 4. Check Device Status
```bash
curl http://localhost:8001/status  # Water Quality
curl http://localhost:8002/status  # Water Level
curl http://localhost:8003/status  # Water Flow
curl http://localhost:8004/status  # Motor
```

### 5. Manually Send Command
```bash
curl -X POST http://localhost:3043/execute/command \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "water_quality_1",
    "plan_code": "TEST_COMMAND",
    "description": "Manual test command"
  }'
```

### 6. View Execution History
```sql
-- In PostgreSQL
SELECT * FROM recent_executions;
SELECT * FROM execution_stats;
```

## Stopping the System

```bash
# Stop all IoT services
./stop_iot_gateway.sh

# Stop MAPE-K (Ctrl+C in its terminal)
```

## Ports Used

| Service | Port | Protocol |
|---------|------|----------|
| IoT Gateway | 3043 | HTTP (FastAPI) |
| Water Quality Sensor | 8001 | HTTP (FastAPI) |
| Water Level Sensor | 8002 | HTTP (FastAPI) |
| Water Flow Sensor | 8003 | HTTP (FastAPI) |
| Motor Sensor | 8004 | HTTP (FastAPI) |
| PostgreSQL | 5432 | PostgreSQL |

## Troubleshooting

### Problem: Gateway won't start
**Solution:** Check if port 3043 is already in use:
```bash
lsof -ti:3043
kill -9 <PID>  # if needed
```

### Problem: Sensor can't connect to Gateway
**Solution:** Ensure Gateway is running first:
```bash
curl http://localhost:3043/
```

### Problem: MAPE-K can't send commands
**Solution:** Verify Gateway URL in `plain_mapek/execute.py`:
```python
GATEWAY_URL = "http://localhost:3043"
```

### Problem: Device not receiving commands
**Solution:** Check device is running and port is correct:
```bash
curl http://localhost:8001/status
```

## Next Steps

1. ✅ **System is ready** - Start services and watch it work!
2. 📊 **Monitor logs** - See data flow and command execution
3. 🔧 **Test commands** - Send manual commands via curl
4. 📈 **View database** - Check execution history
5. 🎯 **Customize** - Add new sensors or commands

## What Makes This Realistic

1. **Device Independence** - Each sensor runs independently
2. **Command Interface** - Devices listen for commands on their own ports
3. **Self-Healing** - Devices fix themselves when commanded
4. **Centralized Control** - Gateway manages all communication
5. **Audit Trail** - All executions logged in database
6. **Error Handling** - Graceful handling of failures
7. **Scalable** - Easy to add new devices

This simulates a **real industrial IoT deployment** where:
- Edge devices have local intelligence
- Central gateway coordinates everything
- MAPE-K provides autonomous control
- System self-heals when problems occur

Enjoy your realistic MAPE-K IoT system! 🚀
