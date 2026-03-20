# IoT Gateway Architecture - MAPE-K System

## Overview

This system implements a realistic IoT architecture with bidirectional communication between sensors and the MAPE-K control loop through a central FastAPI Gateway.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        IoT Sensors (Devices)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Water Quality │  │ Water Level  │  │  Water Flow  │  Motor   │
│  │   :8001      │  │    :8002     │  │    :8003     │  :8004   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──┬────┘
│         │ Send Data       │ Send Data       │ Send Data    │     │
│         └─────────────────┴─────────────────┴──────────────┘     │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   IoT Gateway :3043     │
                    │   (FastAPI Server)      │
                    │  ┌───────────────────┐  │
                    │  │ Data Ingestion    │  │ ◄── Sensors POST data
                    │  │ PostgreSQL Store  │  │
                    │  │ Monitor Endpoints │  │ ◄── MAPE-K reads data
                    │  │ Command Router    │  │ ◄── MAPE-K sends commands
                    │  └───────────────────┘  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   MAPE-K Control Loop   │
                    │  ┌────────────────────┐ │
                    │  │ Monitor  (reads)   │ │
                    │  │ Analyze            │ │
                    │  │ Plan               │ │
                    │  │ Execute (commands) │ │
                    │  │ Knowledge          │ │
                    │  └────────────────────┘ │
                    └─────────────────────────┘
```

## Components

### 1. IoT Gateway (`iot_gateway.py`)
**Port:** 3043

Central FastAPI server that:
- **Receives sensor data** from all IoT devices and stores in PostgreSQL
- **Provides monitoring endpoints** for MAPE-K to fetch latest data
- **Routes execution commands** from MAPE-K to appropriate IoT devices
- **Logs all executions** for audit trail

**Endpoints:**
- Data Ingestion:
  - `POST /iot/water_quality`
  - `POST /iot/water_level`
  - `POST /iot/water_flow`
  - `POST /iot/motor`

- Monitor (MAPE-K reads):
  - `GET /monitor/water_quality/latest?limit=10`
  - `GET /monitor/water_level/latest?limit=10`
  - `GET /monitor/water_flow/latest?limit=10`
  - `GET /monitor/motor/latest?limit=10`

- Command Execution (MAPE-K sends):
  - `POST /execute/command`
    ```json
    {
      "node_id": "water_quality_1",
      "plan_code": "RECALIBRATE_SENSOR",
      "description": "Recalibrate water quality sensor"
    }
    ```

- Health & Status:
  - `GET /` - Health check
  - `GET /devices` - List registered devices
  - `GET /device/{node_id}/status` - Get device status

### 2. IoT Sensor Scripts (Simulated Devices)

Each sensor runs TWO components:
1. **Data Sender** - Continuously sends sensor data to Gateway
2. **Command Receiver** - FastAPI server listening for commands from Gateway

#### Water Quality Sensor (`water_quality_sensor.py`)
- **Data Port:** Sends to Gateway at 3043
- **Command Port:** 8001
- **Sensors:** temperature, tds_voltage, uncompensated_tds, compensated_tds
- **Anomalies:** High temperature (40-60°C), high TDS (600-1000)

#### Water Level Sensor (`water_level_sensor.py`)
- **Data Port:** Sends to Gateway at 3043
- **Command Port:** 8002
- **Sensors:** water_level, temperature
- **Anomalies:** Negative water level (-5 to 0), high temperature

#### Water Flow Sensor (`water_flow_sensor.py`)
- **Data Port:** Sends to Gateway at 3043
- **Command Port:** 8003
- **Sensors:** flowrate, total_flow, pressure, pressure_voltage
- **Anomalies:** High flowrate (15-25), high pressure (6-10)

#### Motor Sensor (`motor_sensor.py`)
- **Data Port:** Sends to Gateway at 3043
- **Command Port:** 8004
- **Sensors:** status, voltage, current, power, energy, frequency, power_factor
- **Anomalies:** Low voltage (180-210V), high current (15-20A), low frequency (45-48Hz)

### 3. MAPE-K Execute Component (`plain_mapek/execute.py`)

Modified to send commands through the IoT Gateway instead of directly to devices.

**Flow:**
1. Execute receives plan from Planner
2. Execute sends command to Gateway at `/execute/command`
3. Gateway routes command to appropriate device based on `node_id`
4. Device receives command and applies fix
5. Device returns to normal operation

## Installation

### Prerequisites
```bash
pip install fastapi uvicorn psycopg2-binary requests pydantic
```

### Database Setup
Ensure PostgreSQL is running and create the execution log table:
```sql
CREATE TABLE IF NOT EXISTS execution_log (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50),
    plan_code VARCHAR(100),
    description TEXT,
    status VARCHAR(20),
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Running the System

### Step 1: Start IoT Gateway
```bash
python iot_gateway.py
```
The gateway will start on port 3043.

### Step 2: Start IoT Sensor Scripts
Open separate terminals for each sensor:

```bash
# Terminal 1
python iot_scripts/water_quality_sensor.py

# Terminal 2
python iot_scripts/water_level_sensor.py

# Terminal 3
python iot_scripts/water_flow_sensor.py

# Terminal 4
python iot_scripts/motor_sensor.py
```

Each sensor will:
- Start its command receiver (FastAPI server)
- Begin sending data to the Gateway every 60 seconds
- Listen for commands from MAPE-K

### Step 3: Start MAPE-K Loop
```bash
cd plain_mapek
python main.py
```

## How It Works

### Normal Operation Flow
1. **Sensors generate data** (30% chance of anomaly)
2. **Sensors POST data** to Gateway endpoints
3. **Gateway stores data** in PostgreSQL
4. **MAPE-K Monitor** fetches latest data from Gateway
5. **MAPE-K Analyze** detects anomalies
6. **MAPE-K Plan** selects appropriate fix
7. **MAPE-K Execute** sends command to Gateway
8. **Gateway routes command** to specific device
9. **Device receives command** and applies fix
10. **Device returns** to normal operation

### Command Execution Example

When water quality sensor has anomalous TDS readings:

```
MAPE-K Execute:
  ↓ POST /execute/command
  {
    "node_id": "water_quality_1",
    "plan_code": "RECALIBRATE_SENSOR",
    "description": "Recalibrate water quality sensor"
  }

IoT Gateway:
  ↓ Routes to device registry
  ↓ Finds device at http://localhost:8001/command
  ↓ POST /command

Water Quality Sensor:
  ↓ Receives command
  ↓ Applies fix (recalibration)
  ↓ Sets fault_fixed = True
  ↓ Starts sending normal values
  ↓ Returns success response
```

### Self-Healing Behavior

1. **Anomaly Detected:** Sensor sends faulty data
2. **Command Received:** MAPE-K sends fix command via Gateway
3. **Fix Applied:** Sensor adjusts and sends normal data for 3 cycles
4. **Recovery Complete:** Sensor can generate new anomalies

This creates a realistic self-healing IoT system!

## Testing Commands

### Check Gateway Health
```bash
curl http://localhost:3043/
```

### List Registered Devices
```bash
curl http://localhost:3043/devices
```

### Get Latest Water Quality Data
```bash
curl http://localhost:3043/monitor/water_quality/latest?limit=5
```

### Manually Send Command to Device
```bash
curl -X POST http://localhost:3043/execute/command \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "water_quality_1",
    "plan_code": "RECALIBRATE_SENSOR",
    "description": "Manual recalibration"
  }'
```

### Check Device Status
```bash
curl http://localhost:8001/status  # Water Quality
curl http://localhost:8002/status  # Water Level
curl http://localhost:8003/status  # Water Flow
curl http://localhost:8004/status  # Motor
```

## Monitoring

### Gateway Logs
The Gateway shows:
- Data ingestion from sensors
- Monitor queries from MAPE-K
- Command routing to devices
- Execution results

### Sensor Logs
Each sensor shows:
- Data cycle number
- Normal/Anomaly/Fixed status
- Commands received
- Fixes applied

### MAPE-K Logs
The Execute component shows:
- Commands sent to Gateway
- Success/failure status
- Error messages if any

## Troubleshooting

### Gateway Cannot Connect to Database
- Check PostgreSQL is running
- Verify database credentials in `iot_gateway.py`
- Ensure database `iot_mapek` exists

### MAPE-K Cannot Connect to Gateway
- Ensure Gateway is running on port 3043
- Check firewall settings
- Verify URL in `plain_mapek/execute.py`

### Gateway Cannot Connect to Device
- Ensure sensor script is running
- Check device is listening on correct port
- Verify device registry in `iot_gateway.py`

### Device Not Receiving Commands
- Check device FastAPI server is running
- Verify port in device registry matches actual port
- Test with manual curl command

## Architecture Benefits

1. **Centralized Control:** Single Gateway manages all device communication
2. **Scalability:** Easy to add new devices to registry
3. **Reliability:** Gateway handles connection failures gracefully
4. **Monitoring:** All data flows through Gateway for logging
5. **Security:** Can add authentication at Gateway level
6. **Testability:** Easy to test with curl commands
7. **Realism:** Mirrors actual IoT deployments
