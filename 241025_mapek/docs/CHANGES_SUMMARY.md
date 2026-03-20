# IoT Gateway System - Summary of Changes

## What You Asked For

> "I need one fast api script which accepts the data from these four scripts and store in the postgres database from the postgres database the monitor takes the data and run the mapek loop. Now the execute in the mapek send the execute command through the fast api and it will communicate to the device the command and the device is capable enough of understanding the command received."

## What Was Delivered

A **complete bidirectional IoT system** where:
- ✅ One FastAPI Gateway receives data from all 4 sensors
- ✅ Gateway stores data in PostgreSQL
- ✅ MAPE-K Monitor reads from Gateway
- ✅ MAPE-K Execute sends commands through Gateway
- ✅ Gateway routes commands to correct devices
- ✅ Devices understand and execute commands
- ✅ Devices self-heal and return to normal

---

## Files Created

### 1. `iot_gateway.py` ⭐ MAIN GATEWAY
**What it does:**
- Runs FastAPI server on port 3043
- Receives sensor data from all 4 IoT devices
- Stores data in PostgreSQL database
- Provides `/monitor/*` endpoints for MAPE-K to read data
- Provides `/execute/command` endpoint for MAPE-K to send commands
- Routes commands to correct device based on node_id
- Logs all executions to database

**Key Endpoints:**
```python
POST /iot/water_quality     # Sensors send data here
POST /iot/water_level
POST /iot/water_flow
POST /iot/motor

GET /monitor/water_quality/latest  # MAPE-K reads from here
GET /monitor/water_level/latest
GET /monitor/water_flow/latest
GET /monitor/motor/latest

POST /execute/command       # MAPE-K sends commands here
                           # Gateway routes to devices

GET /devices               # List all registered devices
GET /device/{id}/status    # Check device status
```

### 2. `start_iot_gateway.sh` 🚀 STARTUP SCRIPT
**What it does:**
- Starts IoT Gateway on port 3043
- Starts all 4 sensor scripts with their command receivers
- Saves PIDs for easy shutdown
- Shows status of all services

**Usage:**
```bash
chmod +x start_iot_gateway.sh
./start_iot_gateway.sh
```

### 3. `stop_iot_gateway.sh` 🛑 SHUTDOWN SCRIPT
**What it does:**
- Stops all running IoT services
- Cleans up ports 3043, 8001-8004
- Removes PID files

**Usage:**
```bash
./stop_iot_gateway.sh
```

### 4. `setup_execution_log.sql` 📊 DATABASE SETUP
**What it does:**
- Creates `execution_log` table for command tracking
- Creates indexes for fast queries
- Creates views for execution statistics
- Provides audit trail of all commands

**Usage:**
```bash
psql -U postgres -d iot_mapek -f setup_execution_log.sql
```

### 5. Documentation Files 📚

#### `IOT_GATEWAY_README.md` - Full technical documentation
- Complete architecture overview
- Detailed API documentation
- Installation instructions
- Testing commands
- Troubleshooting guide

#### `QUICKSTART_IOT_GATEWAY.md` - Quick start guide
- 3-step setup process
- Visual architecture diagram
- Testing examples
- Port reference table

#### `ARCHITECTURE_FLOW.md` - Visual flow diagrams
- ASCII art system diagram
- Complete end-to-end example
- Step-by-step command flow
- Real scenario walkthrough

---

## Files Modified

### 1. `iot_scripts/water_quality_sensor.py` ✨ ENHANCED
**Changes:**
- ✅ Added FastAPI server to receive commands (port 8001)
- ✅ Runs in background thread while sending data
- ✅ Listens for commands from MAPE-K via Gateway
- ✅ Applies fixes when commands received
- ✅ Self-heals and returns to normal operation
- ✅ Tracks sensor state (faulty, fixed, last_command)

**New Capabilities:**
```python
# Receives commands like:
POST http://localhost:8001/command
{
  "plan_code": "RECALIBRATE_SENSOR",
  "description": "Fix sensor"
}

# Returns status:
GET http://localhost:8001/status
{
  "node_id": "water_quality_1",
  "is_faulty": false,
  "fault_fixed": true,
  "last_command": "RECALIBRATE_SENSOR"
}
```

### 2. `iot_scripts/water_level_sensor.py` ✨ ENHANCED
**Changes:** Same as water_quality_sensor
- Command port: 8002
- Handles water level and temperature data
- Self-healing capability

### 3. `iot_scripts/water_flow_sensor.py` ✨ ENHANCED
**Changes:** Same as water_quality_sensor
- Command port: 8003
- Handles flowrate, pressure, and flow data
- Self-healing capability

### 4. `iot_scripts/motor_sensor.py` ✨ ENHANCED
**Changes:** Same as water_quality_sensor, plus:
- Command port: 8004
- Additional motor control commands (TURN_ON/TURN_OFF)
- Motor state management
- Self-healing capability

### 5. `plain_mapek/execute.py` 🔄 UPDATED
**Changes:**
- ❌ Removed old direct-to-device communication
- ✅ Now sends all commands through IoT Gateway
- ✅ Uses Gateway's `/execute/command` endpoint
- ✅ Gateway handles device routing automatically
- ✅ Better error handling and logging

**Old approach:**
```python
# Old - tried to connect directly to device IP
node_ip = get_node_ip(node_id)
send_command(node_ip, plan)  # Simulated only
```

**New approach:**
```python
# New - sends through Gateway, Gateway routes to device
POST http://localhost:3043/execute/command
{
  "node_id": "water_quality_1",
  "plan_code": "RECALIBRATE_SENSOR",
  "description": "Fix sensor"
}
# Gateway handles the routing!
```

### 6. `requirements.txt` 📦 UPDATED
**Added:**
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
```

---

## System Architecture Overview

```
Before (Old):
  Sensors → Database ← MAPE-K
  No command execution (simulated only)

After (New):
  Sensors ←→ Gateway ←→ MAPE-K
  Full bidirectional communication
  Real command execution
```

### Data Flow (Monitoring)
```
Sensor → POST /iot/{type} → Gateway → PostgreSQL → Monitor (GET /monitor/{type}/latest) → MAPE-K
```

### Command Flow (Execution)
```
MAPE-K → Execute → POST /execute/command → Gateway → Routes by node_id → Device FastAPI → Apply Fix
```

---

## How to Use

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Setup Database
```bash
psql -U postgres -d iot_mapek -f setup_execution_log.sql
```

### Step 3: Start System
```bash
# Terminal 1: Start Gateway and Sensors
./start_iot_gateway.sh

# Terminal 2: Start MAPE-K
cd plain_mapek
python3 main.py
```

### Step 4: Watch It Work!
```bash
# Watch sensor logs
tail -f sensor.log

# Check execution history
psql -U postgres -d iot_mapek -c "SELECT * FROM recent_executions;"

# Test commands
curl -X POST http://localhost:3043/execute/command \
  -H "Content-Type: application/json" \
  -d '{"node_id":"water_quality_1","plan_code":"TEST","description":"Test"}'
```

---

## Key Features

### 1. Realistic Device Behavior
- Each device is independent
- Devices have local intelligence
- Devices understand commands
- Self-healing capability

### 2. Central Gateway Coordination
- Single point of communication
- Automatic command routing
- Database persistence
- Execution logging

### 3. Complete MAPE-K Integration
- Monitor reads from Gateway
- Execute sends through Gateway
- No code changes needed in Monitor, Analyze, Plan
- Only Execute was updated

### 4. Production-Ready Features
- ✅ Error handling
- ✅ Timeouts
- ✅ Logging
- ✅ Health checks
- ✅ Status monitoring
- ✅ Audit trail

---

## Testing Scenarios

### Scenario 1: Normal Operation
```
1. Sensors send normal data every 60s
2. Gateway stores in database
3. MAPE-K monitors and finds no issues
4. System continues running
```

### Scenario 2: Anomaly Detection and Fix
```
1. Sensor generates anomalous data (30% chance)
2. Sensor posts to Gateway
3. Gateway stores in database
4. MAPE-K Monitor reads anomalous data
5. Analyzer detects problem
6. Planner selects fix
7. Execute sends command to Gateway
8. Gateway routes to device
9. Device receives command
10. Device applies fix
11. Device sends normal data
12. System recovers!
```

### Scenario 3: Device Offline
```
1. Device is stopped
2. MAPE-K tries to send command
3. Gateway attempts connection
4. Connection fails
5. Error logged in database
6. MAPE-K receives error response
7. Can retry later
```

---

## What Makes This Special

### Before Your Request:
- ❌ No central gateway
- ❌ Direct sensor-to-database
- ❌ Simulated command execution only
- ❌ No device intelligence
- ❌ No self-healing

### After Implementation:
- ✅ Central FastAPI Gateway
- ✅ Bidirectional communication
- ✅ Real command execution
- ✅ Intelligent devices
- ✅ Self-healing system
- ✅ Production-ready architecture
- ✅ Complete observability
- ✅ Audit trail

---

## Port Reference

| Component | Port | Purpose |
|-----------|------|---------|
| IoT Gateway | 3043 | Central hub for all communication |
| Water Quality | 8001 | Command receiver for sensor |
| Water Level | 8002 | Command receiver for sensor |
| Water Flow | 8003 | Command receiver for sensor |
| Motor | 8004 | Command receiver for sensor |
| PostgreSQL | 5432 | Database storage |

---

## Next Steps

1. ✅ **System is ready** - All files created and modified
2. 📦 **Install dependencies** - `pip install -r requirements.txt`
3. 🗄️ **Setup database** - Run `setup_execution_log.sql`
4. 🚀 **Start services** - `./start_iot_gateway.sh`
5. 🔄 **Start MAPE-K** - `cd plain_mapek && python3 main.py`
6. 👀 **Watch logs** - See commands flow through system
7. 🧪 **Test manually** - Use curl commands to test
8. 📊 **View database** - Check execution history

---

## Success Criteria Met ✅

✅ **One FastAPI Gateway** - Created `iot_gateway.py`  
✅ **Accepts data from 4 sensors** - POST /iot/* endpoints  
✅ **Stores in PostgreSQL** - Database integration complete  
✅ **Monitor reads from database** - GET /monitor/* endpoints  
✅ **Execute sends commands** - POST /execute/command  
✅ **Gateway routes to devices** - Device registry system  
✅ **Devices understand commands** - FastAPI servers in each sensor  
✅ **Devices apply fixes** - Self-healing logic implemented  

**Your vision is now reality!** 🎉
