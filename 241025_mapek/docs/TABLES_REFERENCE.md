# 📊 Database Tables - Complete Reference

## Quick Setup

```bash
# Run this ONE command to set up everything:
psql -U postgres -d mapek_dt -f setup_complete_database.sql

# Or use the setup script:
chmod +x setup.sh
./setup.sh
```

---

## 📋 All Tables (11 Total)

### 🌊 SENSOR DATA TABLES (4)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| **water_quality** | Water quality readings | temperature, tds_voltage, uncompensated_tds, compensated_tds |
| **water_level** | Water level readings | water_level, temperature |
| **water_flow** | Flow and pressure readings | flowrate, total_flow, pressure, pressure_voltage |
| **motor** | Motor electrical readings | status, voltage, current, power, energy, frequency, power_factor |

**All have:** `id`, `node_id`, `timestamp`

---

### ⚙️ CONFIGURATION TABLES (3)

| Table | Purpose | Pre-populated? |
|-------|---------|----------------|
| **nodes** | Device registry | ✅ Yes (4 nodes) |
| **thresholds** | Anomaly detection rules | ✅ Yes (15 thresholds) |
| **plans** | Action plans for states | ✅ Yes (15 plans) |

---

### 📝 MAPE-K LOG TABLES (3)

| Table | Component | Records |
|-------|-----------|---------|
| **analyze** | Analyzer | Analysis results and detected states |
| **plan_selection** | Planner | Which plans were selected |
| **execution** | Executor | Execution results from MAPE-K |

---

### 🌐 GATEWAY LOG TABLE (1)

| Table | Purpose |
|-------|---------|
| **execution_log** | Commands sent through IoT Gateway to devices |

---

## 🔄 Data Flow Through Tables

```
1. SENSOR SENDS DATA
   ↓
   IoT Gateway receives
   ↓
   INSERT INTO water_quality/water_level/water_flow/motor

2. MONITOR READS
   ↓
   SELECT FROM water_quality WHERE node_id = 'xxx' ORDER BY timestamp DESC LIMIT 1
   ↓
   Passes to Analyzer

3. ANALYZE COMPARES
   ↓
   SELECT FROM thresholds
   ↓
   Compare sensor values with thresholds
   ↓
   INSERT INTO analyze (result, state)

4. PLAN SELECTS
   ↓
   SELECT FROM plans WHERE state = 'detected_state'
   ↓
   INSERT INTO plan_selection (plan_code)

5. EXECUTE COMMANDS
   ↓
   POST to IoT Gateway /execute/command
   ↓
   Gateway routes to device
   ↓
   INSERT INTO execution (status, message)
   INSERT INTO execution_log (status, error_message)
```

---

## 📊 Table Details

### 1. water_quality
```sql
CREATE TABLE water_quality (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    temperature FLOAT NOT NULL,           -- °C
    tds_voltage FLOAT NOT NULL,           -- V
    uncompensated_tds FLOAT NOT NULL,     -- ppm
    compensated_tds FLOAT NOT NULL,       -- ppm
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Used by:** IoT Gateway (INSERT), Monitor (SELECT)

### 2. water_level
```sql
CREATE TABLE water_level (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    water_level FLOAT NOT NULL,           -- cm
    temperature FLOAT NOT NULL,           -- °C
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Used by:** IoT Gateway (INSERT), Monitor (SELECT)

### 3. water_flow
```sql
CREATE TABLE water_flow (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    flowrate FLOAT NOT NULL,              -- L/min
    total_flow FLOAT NOT NULL,            -- L
    pressure FLOAT NOT NULL,              -- bar
    pressure_voltage FLOAT NOT NULL,      -- V
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Used by:** IoT Gateway (INSERT), Monitor (SELECT)

### 4. motor
```sql
CREATE TABLE motor (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    status VARCHAR(10) NOT NULL,          -- 'ON' or 'OFF'
    voltage FLOAT NOT NULL,               -- V
    current FLOAT NOT NULL,               -- A
    power FLOAT NOT NULL,                 -- W
    energy FLOAT NOT NULL,                -- kWh
    frequency FLOAT NOT NULL,             -- Hz
    power_factor FLOAT NOT NULL,          -- 0-1
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Used by:** IoT Gateway (INSERT), Monitor (SELECT)

### 5. nodes
```sql
CREATE TABLE nodes (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) UNIQUE NOT NULL,
    node_type VARCHAR(50) NOT NULL,
    ip_address VARCHAR(50),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Pre-populated with:**
- water_quality_1 (localhost:8001)
- water_level_1 (localhost:8002)
- water_flow_1 (localhost:8003)
- motor_1 (localhost:8004)

**Used by:** Reference, can be used by Monitor to get active nodes

### 6. thresholds
```sql
CREATE TABLE thresholds (
    id SERIAL PRIMARY KEY,
    parameter VARCHAR(100) UNIQUE NOT NULL,
    min_value FLOAT,
    max_value FLOAT,
    description TEXT
);
```
**Pre-populated with 15 thresholds:**
- temperature: 15.0 - 35.0
- tds_voltage: 0.0 - 3.0
- water_level: 0.0 - 15.0
- voltage: 210.0 - 250.0
- etc.

**Used by:** Analyzer (SELECT to compare sensor values)

### 7. plans
```sql
CREATE TABLE plans (
    id SERIAL PRIMARY KEY,
    state VARCHAR(50) NOT NULL,
    plan_code VARCHAR(100) NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 1,
    UNIQUE (state, plan_code)
);
```
**Pre-populated with 15 plans:**
- HIGH_TEMPERATURE → ACTIVATE_COOLING
- LOW_WATER_LEVEL → ACTIVATE_PUMP
- HIGH_TDS → RECALIBRATE_SENSOR
- etc.

**Used by:** Planner (SELECT to find action for detected state)

### 8. analyze
```sql
CREATE TABLE analyze (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    result TEXT,
    state VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Used by:** Analyzer (INSERT analysis results)

### 9. plan_selection
```sql
CREATE TABLE plan_selection (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    plan_code VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Used by:** Planner (INSERT selected plan)

### 10. execution
```sql
CREATE TABLE execution (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    plan_code VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Used by:** Executor (INSERT execution results)

### 11. execution_log
```sql
CREATE TABLE execution_log (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    plan_code VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Used by:** IoT Gateway (INSERT when routing commands to devices)

---

## 🔍 Useful Queries

### Check if tables exist
```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
```

### Count rows in all tables
```sql
SELECT 'water_quality' as table_name, COUNT(*) as rows FROM water_quality
UNION ALL SELECT 'water_level', COUNT(*) FROM water_level
UNION ALL SELECT 'water_flow', COUNT(*) FROM water_flow
UNION ALL SELECT 'motor', COUNT(*) FROM motor
UNION ALL SELECT 'nodes', COUNT(*) FROM nodes
UNION ALL SELECT 'thresholds', COUNT(*) FROM thresholds
UNION ALL SELECT 'plans', COUNT(*) FROM plans
UNION ALL SELECT 'analyze', COUNT(*) FROM analyze
UNION ALL SELECT 'plan_selection', COUNT(*) FROM plan_selection
UNION ALL SELECT 'execution', COUNT(*) FROM execution
UNION ALL SELECT 'execution_log', COUNT(*) FROM execution_log;
```

### View recent sensor data
```sql
SELECT * FROM water_quality ORDER BY timestamp DESC LIMIT 5;
```

### View MAPE-K activity
```sql
-- What did Analyzer find?
SELECT * FROM analyze ORDER BY timestamp DESC LIMIT 10;

-- What plans were selected?
SELECT * FROM plan_selection ORDER BY timestamp DESC LIMIT 10;

-- What was executed?
SELECT * FROM execution ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM execution_log ORDER BY timestamp DESC LIMIT 10;
```

### View configuration
```sql
SELECT * FROM thresholds;
SELECT * FROM plans ORDER BY state, priority DESC;
SELECT * FROM nodes WHERE is_active = true;
```

---

## ✅ Verification Checklist

After running `setup_complete_database.sql`, verify:

- [ ] All 11 tables exist
- [ ] `thresholds` has 15 rows
- [ ] `plans` has 15 rows
- [ ] `nodes` has 4 rows
- [ ] Sensor tables are empty (will be filled by sensors)
- [ ] Log tables are empty (will be filled by MAPE-K)

Run this:
```sql
-- Should return 11 tables
SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';

-- Should return counts
SELECT 
    (SELECT COUNT(*) FROM thresholds) as thresholds,
    (SELECT COUNT(*) FROM plans) as plans,
    (SELECT COUNT(*) FROM nodes) as nodes;
```

---

## 🎯 Which Component Uses Which Table?

| Component | Tables Used | Operation |
|-----------|-------------|-----------|
| **IoT Sensors** | water_quality, water_level, water_flow, motor | Send data |
| **IoT Gateway** | All sensor tables, execution_log | INSERT sensor data, log commands |
| **Monitor** | All sensor tables | SELECT latest readings |
| **Analyzer** | thresholds, analyze | SELECT rules, INSERT results |
| **Planner** | plans, plan_selection | SELECT actions, INSERT choices |
| **Executor** | execution | INSERT execution results |
| **Gateway Execute** | execution_log | INSERT command routing logs |

---

## 📁 Files You Need

| File | Purpose |
|------|---------|
| `setup_complete_database.sql` | **Main setup script** - Creates all 11 tables |
| `DATABASE_SCHEMA.md` | This documentation |
| `setup.sh` | Automated setup script (runs SQL + checks) |

---

## 🚀 Quick Start

```bash
# 1. Create database
createdb mapek_dt

# 2. Run setup
psql -U postgres -d mapek_dt -f setup_complete_database.sql

# 3. Verify
psql -U postgres -d mapek_dt -c "SELECT tablename FROM pg_tables WHERE schemaname='public';"

# 4. Done! ✅
```

---

## 💡 Remember

- **Database name:** `mapek_dt` (used by both MAPE-K and IoT Gateway)
- **Setup file:** `setup_complete_database.sql`
- **All tables:** Created in one go
- **Pre-populated:** thresholds, plans, and nodes
- **Empty tables:** sensor data and logs (filled during operation)

**You're all set! The database is ready for your IoT MAPE-K system! 🎉**
