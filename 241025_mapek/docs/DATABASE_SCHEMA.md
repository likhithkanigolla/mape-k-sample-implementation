# Database Schema - IoT MAPE-K System

## Database Name
**Default:** `mapek_dt`  
**Note:** IoT Gateway uses `iot_mapek` - you can use either, just update config files accordingly.

---

## 📊 Database Tables Overview

### 1️⃣ SENSOR DATA TABLES (4 tables)
These store incoming data from IoT sensors.

#### `water_quality`
Stores water quality sensor readings.
```sql
- id (SERIAL PRIMARY KEY)
- node_id (VARCHAR) - Sensor identifier
- temperature (FLOAT) - Water temperature (°C)
- tds_voltage (FLOAT) - TDS sensor voltage (V)
- uncompensated_tds (FLOAT) - Raw TDS value (ppm)
- compensated_tds (FLOAT) - Temperature-compensated TDS (ppm)
- timestamp (TIMESTAMP) - When data was recorded
```

#### `water_level`
Stores water level sensor readings.
```sql
- id (SERIAL PRIMARY KEY)
- node_id (VARCHAR) - Sensor identifier
- water_level (FLOAT) - Water level (cm)
- temperature (FLOAT) - Water temperature (°C)
- timestamp (TIMESTAMP) - When data was recorded
```

#### `water_flow`
Stores water flow sensor readings.
```sql
- id (SERIAL PRIMARY KEY)
- node_id (VARCHAR) - Sensor identifier
- flowrate (FLOAT) - Flow rate (L/min)
- total_flow (FLOAT) - Total flow volume (L)
- pressure (FLOAT) - Water pressure (bar)
- pressure_voltage (FLOAT) - Pressure sensor voltage (V)
- timestamp (TIMESTAMP) - When data was recorded
```

#### `motor`
Stores motor sensor readings.
```sql
- id (SERIAL PRIMARY KEY)
- node_id (VARCHAR) - Motor identifier
- status (VARCHAR) - 'ON' or 'OFF'
- voltage (FLOAT) - Supply voltage (V)
- current (FLOAT) - Current draw (A)
- power (FLOAT) - Power consumption (W)
- energy (FLOAT) - Energy used (kWh)
- frequency (FLOAT) - Supply frequency (Hz)
- power_factor (FLOAT) - Power factor (0-1)
- timestamp (TIMESTAMP) - When data was recorded
```

---

### 2️⃣ MAPE-K CONFIGURATION TABLES (3 tables)
These define rules and thresholds for the MAPE-K loop.

#### `nodes`
Registry of all IoT nodes in the system.
```sql
- id (SERIAL PRIMARY KEY)
- node_id (VARCHAR UNIQUE) - Unique node identifier
- node_type (VARCHAR) - Type of sensor/device
- ip_address (VARCHAR) - Device IP/port
- description (TEXT) - Human-readable description
- is_active (BOOLEAN) - Whether node is active
- registered_at (TIMESTAMP) - Registration time
```

#### `thresholds`
Defines normal operating ranges for anomaly detection.
```sql
- id (SERIAL PRIMARY KEY)
- parameter (VARCHAR UNIQUE) - Parameter name
- min_value (FLOAT) - Minimum acceptable value
- max_value (FLOAT) - Maximum acceptable value
- description (TEXT) - What this threshold represents
```

**Example data:**
```
temperature: 15.0 - 35.0 °C
voltage: 210.0 - 250.0 V
water_level: 0.0 - 15.0 cm
```

#### `plans`
Action plans for different system states.
```sql
- id (SERIAL PRIMARY KEY)
- state (VARCHAR) - System state that triggers this plan
- plan_code (VARCHAR) - Code identifying the action
- description (TEXT) - What the plan does
- priority (INTEGER) - Higher = more important
```

**Example data:**
```
state: HIGH_TEMPERATURE → plan_code: ACTIVATE_COOLING
state: LOW_WATER_LEVEL → plan_code: ACTIVATE_PUMP
state: HIGH_TDS → plan_code: RECALIBRATE_SENSOR
```

---

### 3️⃣ MAPE-K EXECUTION LOGS (3 tables)
These track what the MAPE-K loop does.

#### `analyze`
Logs analysis results from the Analyze component.
```sql
- id (SERIAL PRIMARY KEY)
- node_id (VARCHAR) - Which node was analyzed
- result (TEXT) - Analysis findings
- state (VARCHAR) - Detected state (NORMAL, HIGH_TDS, etc.)
- timestamp (TIMESTAMP) - When analysis occurred
```

#### `plan_selection`
Logs which plans were selected by the Plan component.
```sql
- id (SERIAL PRIMARY KEY)
- node_id (VARCHAR) - Which node needs action
- plan_code (VARCHAR) - Which plan was selected
- timestamp (TIMESTAMP) - When plan was selected
```

#### `execution`
Logs execution results from the Execute component.
```sql
- id (SERIAL PRIMARY KEY)
- node_id (VARCHAR) - Which node received command
- plan_code (VARCHAR) - Which plan was executed
- status (VARCHAR) - 'success', 'failed', 'error'
- message (TEXT) - Execution result message
- timestamp (TIMESTAMP) - When execution occurred
```

---

### 4️⃣ IOT GATEWAY LOG (1 table)
Tracks commands sent through the IoT Gateway.

#### `execution_log`
Detailed log of all commands routed to devices.
```sql
- id (SERIAL PRIMARY KEY)
- node_id (VARCHAR) - Target device
- plan_code (VARCHAR) - Command sent
- description (TEXT) - Command description
- status (VARCHAR) - 'success' or 'failed'
- error_message (TEXT) - Error details if failed
- timestamp (TIMESTAMP) - When command was sent
```

---

## 🔍 Useful Views

The setup script also creates several views for easy monitoring:

### `recent_sensor_data`
Shows sensor readings from the last hour.

### `recent_executions`
Shows last 100 command executions.

### `execution_stats`
Statistics per node: total executions, success/fail counts.

### `mapek_stats`
Statistics for each MAPE-K component.

### `anomaly_rate`
Percentage of anomalies detected per node.

---

## 📥 How Data Flows

### 1. Sensor → Database
```
IoT Sensor → IoT Gateway (FastAPI) → INSERT INTO water_quality
```

### 2. Monitor Reads
```
MAPE-K Monitor → SELECT FROM water_quality WHERE node_id = 'xxx' ORDER BY timestamp DESC LIMIT 1
```

### 3. Analyze Detects
```
Analyzer → Compare with thresholds → INSERT INTO analyze (result, state)
```

### 4. Plan Selects
```
Planner → SELECT FROM plans WHERE state = 'detected_state' → INSERT INTO plan_selection
```

### 5. Execute Commands
```
Executor → POST to Gateway → Gateway routes to device → INSERT INTO execution_log
```

---

## 🚀 Setup Instructions

### Step 1: Create Database
```bash
# Create database (choose one name)
createdb mapek_dt
# OR
createdb iot_mapek
```

### Step 2: Run Setup Script
```bash
psql -U postgres -d mapek_dt -f setup_complete_database.sql
```

### Step 3: Verify Tables
```bash
psql -U postgres -d mapek_dt -c "\dt"
```

### Step 4: Update Configuration

#### For MAPE-K (plain_mapek/knowledge.py):
```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'mapek_dt',  # ← Your database name
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432
}
```

#### For IoT Gateway (iot_gateway.py):
```python
DB_CONFIG = {
    "host": "localhost",
    "database": "iot_mapek",  # ← Your database name (or mapek_dt)
    "user": "postgres",
    "password": "postgres"
}
```

**Note:** You can use the same database for both, just make sure both config files point to the same database name!

---

## 📊 Table Relationships

```
Sensor Data Tables          MAPE-K Tables           Gateway Table
─────────────────          ─────────────           ─────────────
water_quality    ←────┐
water_level      ←────┤
water_flow       ←────┼──→ Monitor reads    
motor            ←────┘    
                           ↓
                      thresholds ──→ Analyzer compares
                           ↓
                      analyze ──────→ stores results
                           ↓
                      plans ────────→ Planner selects
                           ↓
                      plan_selection → stores choice
                           ↓
                      execution ─────→ Execute logs
                           ↓
                      execution_log ─→ Gateway logs commands
                           ↓
                      (back to devices via Gateway)
```

---

## 🧪 Testing Queries

### Check sensor data
```sql
SELECT * FROM water_quality ORDER BY timestamp DESC LIMIT 5;
SELECT * FROM water_level ORDER BY timestamp DESC LIMIT 5;
SELECT * FROM water_flow ORDER BY timestamp DESC LIMIT 5;
SELECT * FROM motor ORDER BY timestamp DESC LIMIT 5;
```

### Check MAPE-K operations
```sql
SELECT * FROM analyze ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM plan_selection ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM execution ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM execution_log ORDER BY timestamp DESC LIMIT 10;
```

### View statistics
```sql
SELECT * FROM execution_stats;
SELECT * FROM mapek_stats;
SELECT * FROM anomaly_rate;
SELECT * FROM recent_executions LIMIT 20;
```

### Check configuration
```sql
SELECT * FROM thresholds;
SELECT * FROM plans;
SELECT * FROM nodes;
```

---

## 📝 Summary

**Total Tables: 11**

1. ✅ `water_quality` - Water quality sensor data
2. ✅ `water_level` - Water level sensor data
3. ✅ `water_flow` - Water flow sensor data
4. ✅ `motor` - Motor sensor data
5. ✅ `nodes` - Node registry
6. ✅ `thresholds` - Anomaly detection rules
7. ✅ `plans` - Action plans
8. ✅ `analyze` - Analysis log
9. ✅ `plan_selection` - Plan selection log
10. ✅ `execution` - Execution log (MAPE-K)
11. ✅ `execution_log` - Execution log (Gateway)

**All tables are created by running:** `setup_complete_database.sql`

---

## ⚠️ Important Notes

1. **Database Name:** Choose either `mapek_dt` or `iot_mapek` and use consistently
2. **Update Configs:** Make sure `knowledge.py` and `iot_gateway.py` use the same database
3. **Default Data:** Script pre-populates thresholds, plans, and nodes
4. **Indexes:** Optimized indexes are created for fast queries
5. **Views:** Useful views are created for monitoring and statistics
