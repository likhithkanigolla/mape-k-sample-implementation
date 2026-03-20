# IoT MAPE-K System with FastAPI Gateway

A complete bidirectional IoT system implementing the MAPE-K (Monitor-Analyze-Plan-Execute-Knowledge) autonomous control loop with a central FastAPI gateway for device communication.

## 🚀 Quick Start

```bash
# 1. Setup (run once)
./scripts/setup.sh

# 2. Start IoT Gateway and Sensors
./scripts/start_iot_gateway.sh

# 3. Start MAPE-K (in new terminal)
cd plain_mapek && python3 main.py

# 4. Test the system
python3 test_system.py

# 5. Stop everything
./scripts/stop_iot_gateway.sh
```

## 📁 Project Structure

```
241025_mapek/
├── 📂 scripts/              # Shell scripts for system management
│   ├── setup.sh             # Complete system setup
│   ├── start_iot_gateway.sh # Start gateway and sensors
│   ├── stop_iot_gateway.sh  # Stop all services
│   ├── start_all.sh         # Original startup script
│   └── stop_all.sh          # Original stop script
│
├── 📂 docs/                 # Complete documentation
│   ├── README_COMPLETE.md        # 🌟 START HERE - Complete overview
│   ├── QUICKSTART_IOT_GATEWAY.md # Quick start guide
│   ├── IOT_GATEWAY_README.md     # Full technical documentation
│   ├── ARCHITECTURE_FLOW.md      # System architecture diagrams
│   ├── DATABASE_SCHEMA.md        # Database documentation
│   ├── TABLES_REFERENCE.md       # Table quick reference
│   ├── CHANGES_SUMMARY.md        # What was changed/created
│   ├── QUICKSTART.md             # Original quick start
│   ├── README.md                 # Original README
│   └── REORGANIZATION.md         # Original reorganization notes
│
├── 📂 iot_scripts/          # IoT sensor simulators (with command receivers)
│   ├── water_quality_sensor.py   # Port 8001
│   ├── water_level_sensor.py     # Port 8002
│   ├── water_flow_sensor.py      # Port 8003
│   └── motor_sensor.py           # Port 8004
│
├── 📂 plain_mapek/          # MAPE-K control loop
│   ├── main.py              # Main MAPE-K loop
│   ├── monitor.py           # Monitor component
│   ├── analyze.py           # Analyze component
│   ├── plan.py              # Plan component
│   ├── execute.py           # Execute component (uses Gateway)
│   ├── knowledge.py         # Database connection
│   └── logger.py            # Logging utilities
│
├── iot_gateway.py           # 🌟 Central FastAPI Gateway (Port 3043)
├── test_system.py           # Integration tests
├── requirements.txt         # Python dependencies
├── setup_complete_database.sql  # Complete database setup
├── setup_execution_log.sql      # Gateway execution log setup
└── README.md                # This file
```

## 🎯 System Architecture

```
┌─────────────────────────────────────────┐
│   IoT Sensors (4 devices)               │
│   • Water Quality :8001                 │
│   • Water Level :8002                   │
│   • Water Flow :8003                    │
│   • Motor :8004                         │
└──────────────┬──────────────────────────┘
               │ Send data
               ↓
┌─────────────────────────────────────────┐
│   IoT Gateway :3043 (FastAPI)           │
│   • Receives sensor data                │
│   • Stores in PostgreSQL                │
│   • Routes commands to devices          │
└──────────────┬──────────────────────────┘
               │ Monitor reads / Execute sends
               ↓
┌─────────────────────────────────────────┐
│   MAPE-K Control Loop                   │
│   Monitor → Analyze → Plan → Execute    │
└─────────────────────────────────────────┘
```

## 📚 Documentation

**Start with these docs in order:**

1. **[docs/README_COMPLETE.md](docs/README_COMPLETE.md)** - Complete system overview
2. **[docs/QUICKSTART_IOT_GATEWAY.md](docs/QUICKSTART_IOT_GATEWAY.md)** - Quick start guide
3. **[docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)** - Database setup
4. **[docs/IOT_GATEWAY_README.md](docs/IOT_GATEWAY_README.md)** - Full technical docs
5. **[docs/ARCHITECTURE_FLOW.md](docs/ARCHITECTURE_FLOW.md)** - System flow diagrams

## 🔧 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL
- pip

### Setup Steps

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Create database and tables
psql -U postgres -c "CREATE DATABASE mapek_dt;"
psql -U postgres -d mapek_dt -f setup_complete_database.sql

# 3. Make scripts executable
chmod +x scripts/*.sh

# 4. Done! ✅
```

Or use the automated setup:
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## 🎮 Usage

### Start the System

```bash
# Terminal 1: Start Gateway and Sensors
./scripts/start_iot_gateway.sh

# Terminal 2: Start MAPE-K
cd plain_mapek
python3 main.py
```

### Monitor the System

```bash
# Test all components
python3 test_system.py

# Check Gateway
curl http://localhost:3043/

# Check device status
curl http://localhost:8001/status

# View execution logs
psql -U postgres -d mapek_dt -c "SELECT * FROM recent_executions LIMIT 10;"
```

### Stop the System

```bash
./scripts/stop_iot_gateway.sh
# Ctrl+C in MAPE-K terminal
```

## 🗄️ Database Tables

**11 tables total:**

- **Sensor Data (4):** water_quality, water_level, water_flow, motor
- **Configuration (3):** nodes, thresholds, plans
- **MAPE-K Logs (3):** analyze, plan_selection, execution
- **Gateway Log (1):** execution_log

See [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) for complete details.

## 🌟 Key Features

- ✅ **Bidirectional Communication** - Sensors send data, receive commands
- ✅ **Central Gateway** - FastAPI server manages all device communication
- ✅ **Self-Healing** - Devices automatically fix themselves when commanded
- ✅ **Complete MAPE-K** - Full autonomous control loop
- ✅ **Database Logging** - All operations tracked in PostgreSQL
- ✅ **Easy Management** - Simple scripts to start/stop everything
- ✅ **Integration Tests** - Automated testing suite
- ✅ **Production Ready** - Error handling, timeouts, logging

## 📊 Port Reference

| Service | Port | URL |
|---------|------|-----|
| IoT Gateway | 3043 | http://localhost:3043 |
| Water Quality | 8001 | http://localhost:8001 |
| Water Level | 8002 | http://localhost:8002 |
| Water Flow | 8003 | http://localhost:8003 |
| Motor | 8004 | http://localhost:8004 |

## 🧪 Testing

```bash
# Run all integration tests
python3 test_system.py

# Manual tests
curl http://localhost:3043/devices
curl "http://localhost:3043/monitor/water_quality/latest?limit=3"
curl -X POST http://localhost:3043/execute/command \
  -H "Content-Type: application/json" \
  -d '{"node_id":"water_quality_1","plan_code":"TEST","description":"Test command"}'
```

## 📖 How It Works

1. **Sensors generate data** (30% chance of anomaly)
2. **Sensors POST to Gateway** → Gateway stores in database
3. **MAPE-K Monitor reads** from Gateway
4. **Analyzer detects anomalies** using thresholds
5. **Planner selects fix** from plans table
6. **Executor sends command** to Gateway
7. **Gateway routes to device** based on node_id
8. **Device receives and executes** command
9. **Device self-heals** and returns to normal
10. **System continues monitoring** 🔄

See [docs/ARCHITECTURE_FLOW.md](docs/ARCHITECTURE_FLOW.md) for detailed flow diagrams.

## 🤝 Contributing

This is a research/educational project demonstrating:
- IoT device management
- Autonomous control systems (MAPE-K)
- Microservices architecture
- Self-healing systems
- FastAPI web services

## 📄 License

Educational/Research Project

## 🆘 Troubleshooting

### Gateway won't start
```bash
lsof -ti:3043 | xargs kill -9
```

### Database connection error
```bash
# Check database exists
psql -U postgres -l | grep mapek_dt

# Recreate if needed
psql -U postgres -d mapek_dt -f setup_complete_database.sql
```

### Sensors not responding
```bash
# Check if running
lsof -ti:8001,8002,8003,8004

# Restart
./scripts/stop_iot_gateway.sh
./scripts/start_iot_gateway.sh
```

See [docs/IOT_GATEWAY_README.md](docs/IOT_GATEWAY_README.md) for more troubleshooting.

## 📞 Quick Commands Reference

```bash
# Setup
./scripts/setup.sh

# Start
./scripts/start_iot_gateway.sh
cd plain_mapek && python3 main.py

# Test
python3 test_system.py

# Monitor
psql -U postgres -d mapek_dt -c "SELECT * FROM recent_executions;"

# Stop
./scripts/stop_iot_gateway.sh
```

## 🎓 Learn More

- **Complete Documentation:** [docs/](docs/)
- **Database Schema:** [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
- **System Architecture:** [docs/ARCHITECTURE_FLOW.md](docs/ARCHITECTURE_FLOW.md)
- **Change Log:** [docs/CHANGES_SUMMARY.md](docs/CHANGES_SUMMARY.md)

---

**Built with:** Python, FastAPI, PostgreSQL, MAPE-K Architecture

**Status:** ✅ Production Ready

**Last Updated:** October 24, 2025
