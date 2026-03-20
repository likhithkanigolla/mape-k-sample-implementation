# 🚀 Quick Start Guide - Plain MAPE-K System

## ⚡ 60-Second Setup

### 1️⃣ Install Dependencies
```bash
cd /Users/likhithkanigolla/IIITH/code-files/Digital-Twin/mape-k/241025_mapek
pip install -r requirements.txt
```

### 2️⃣ Prerequisites Check
- [ ] PostgreSQL running on `localhost:5432`
- [ ] Database `mapek_dt` exists
- [ ] FastAPI server running on port `3043`

### 3️⃣ Start FastAPI Server (if not running)
```bash
cd ../app
uvicorn main:app --host 0.0.0.0 --port 3043 &
```

### 4️⃣ Start Plain MAPE-K System
```bash
cd /Users/likhithkanigolla/IIITH/code-files/Digital-Twin/mape-k/241025_mapek

# Make scripts executable
chmod +x start_all.sh stop_all.sh

# Start everything
./start_all.sh
```

### 5️⃣ Monitor the System
```bash
# Watch MAPE-K logs
tail -f logs/plain_mapek.log

# Watch all logs
tail -f logs/*.log
```

### 6️⃣ Stop the System
```bash
./stop_all.sh
```

---

## 📂 File Map

| File | Purpose |
|------|---------|
| `plain_mapek/main.py` | Main MAPE-K loop |
| `plain_mapek/monitor.py` | Monitor component |
| `plain_mapek/analyze.py` | Analyze component |
| `plain_mapek/plan.py` | Plan component |
| `plain_mapek/execute.py` | Execute component |
| `plain_mapek/knowledge.py` | Database utilities |
| `plain_mapek/logger.py` | Logging config |
| `iot_scripts/*.py` | IoT sensor simulators |
| `start_all.sh` | Start everything |
| `stop_all.sh` | Stop everything |

---

## 🎯 Manual Start (Alternative)

### Start IoT Sensors
```bash
cd iot_scripts

# Terminal 1
python water_quality_sensor.py

# Terminal 2
python water_flow_sensor.py

# Terminal 3
python water_level_sensor.py

# Terminal 4
python motor_sensor.py
```

### Start MAPE-K Loop
```bash
# Terminal 5
cd plain_mapek
python main.py
```

---

## 🔧 Customization

### Change cycle interval (main.py)
```python
mapek.run(interval=30)  # 30 seconds instead of 60
```

### Change sensor interval (sensor scripts)
```python
time.sleep(30)  # 30 seconds instead of 60
```

### Change anomaly rate (sensor scripts)
```python
if random.random() < 0.5:  # 50% instead of 30%
```

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Database connection error" | Check PostgreSQL: `pg_isready` |
| "Error sending data" | Check FastAPI on port 3043 |
| "No sensor data" | Wait 60 seconds for first cycle |
| "Permission denied" | Run `chmod +x *.sh` |

---

## 📊 Expected Output

```
====================================
Plain MAPE-K System Initialized
====================================

============================================================
MAPE-K Cycle #1 - 2025-10-24 12:00:00
============================================================

[1] MONITOR Phase
Monitor: Read data from 4 sensors

[2] ANALYZE Phase
Analyzer: water_quality_1 - State: normal (0/4 violations)
Analyzer: water_flow_1 - State: warning (1/4 violations)
Analyzer: water_level_1 - State: normal (0/2 violations)
Analyzer: motor_1 - State: critical (3/7 violations)

[3] PLAN Phase
Planner: Selected plan 'PLAN_NORMAL' for water_quality_1
Planner: Selected plan 'PLAN_WARNING' for water_flow_1
Planner: Selected plan 'PLAN_CRITICAL' for motor_1

[4] EXECUTE Phase
Executor: Executed plan 'PLAN_WARNING' for water_flow_1
Executor: Executed plan 'PLAN_CRITICAL' for motor_1

============================================================
Cycle #1 completed successfully
============================================================

Waiting 60 seconds until next cycle...
```

---

## 📚 More Info

- **Full README**: `README.md`
- **Reorganization Details**: `REORGANIZATION.md`
- **Pattern-Based Version**: `/mapek` folder

---

**Created**: October 24, 2025  
**Location**: `/241025_mapek/`
