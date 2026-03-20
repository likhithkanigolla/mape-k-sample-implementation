# 📁 Workspace Organization

Your IoT MAPE-K workspace is now organized! 🎉

## 📂 Directory Structure

```
241025_mapek/
│
├── 📄 README.md                        ← Start here!
├── 📄 iot_gateway.py                   ← Central Gateway (Port 3043)
├── 📄 test_system.py                   ← Integration tests
├── 📄 requirements.txt                 ← Python dependencies
├── 📄 setup_complete_database.sql      ← Database setup (main)
├── 📄 setup_execution_log.sql          ← Gateway log setup
│
├── 📂 scripts/                         ← All shell scripts
│   ├── setup.sh                        ← Complete system setup
│   ├── start_iot_gateway.sh            ← Start gateway + sensors
│   ├── stop_iot_gateway.sh             ← Stop all services
│   ├── start_all.sh                    ← Original start script
│   └── stop_all.sh                     ← Original stop script
│
├── 📂 docs/                            ← All documentation
│   ├── README_COMPLETE.md              ← 🌟 Complete overview
│   ├── QUICKSTART_IOT_GATEWAY.md       ← Quick start guide
│   ├── IOT_GATEWAY_README.md           ← Full technical docs
│   ├── ARCHITECTURE_FLOW.md            ← System diagrams
│   ├── DATABASE_SCHEMA.md              ← Database documentation
│   ├── TABLES_REFERENCE.md             ← Table reference
│   ├── CHANGES_SUMMARY.md              ← Change log
│   ├── QUICKSTART.md                   ← Original quickstart
│   ├── README.md                       ← Original README
│   └── REORGANIZATION.md               ← Original reorg notes
│
├── 📂 iot_scripts/                     ← IoT sensor simulators
│   ├── water_quality_sensor.py         ← Port 8001
│   ├── water_level_sensor.py           ← Port 8002
│   ├── water_flow_sensor.py            ← Port 8003
│   └── motor_sensor.py                 ← Port 8004
│
└── 📂 plain_mapek/                     ← MAPE-K control loop
    ├── main.py                         ← Main loop
    ├── monitor.py                      ← Monitor component
    ├── analyze.py                      ← Analyze component
    ├── plan.py                         ← Plan component
    ├── execute.py                      ← Execute component
    ├── knowledge.py                    ← Database connection
    └── logger.py                       ← Logging utilities
```

## 🚀 Quick Commands

```bash
# Setup (first time)
chmod +x scripts/*.sh
./scripts/setup.sh

# Start system
./scripts/start_iot_gateway.sh
cd plain_mapek && python3 main.py

# Test
python3 test_system.py

# Stop
./scripts/stop_iot_gateway.sh
```

## 📚 Documentation Guide

**Read in this order:**

1. `README.md` (root) - Overview and quick start
2. `docs/README_COMPLETE.md` - Complete system guide
3. `docs/QUICKSTART_IOT_GATEWAY.md` - Detailed quick start
4. `docs/DATABASE_SCHEMA.md` - Database setup
5. `docs/IOT_GATEWAY_README.md` - Gateway documentation
6. `docs/ARCHITECTURE_FLOW.md` - Architecture diagrams

## 🔧 Script Reference

| Script | Purpose |
|--------|---------|
| `scripts/setup.sh` | Complete automated setup |
| `scripts/start_iot_gateway.sh` | Start gateway + 4 sensors |
| `scripts/stop_iot_gateway.sh` | Stop all IoT services |
| `scripts/start_all.sh` | Original startup script |
| `scripts/stop_all.sh` | Original stop script |

## 📖 Documentation Reference

| Document | Content |
|----------|---------|
| `docs/README_COMPLETE.md` | Complete overview with visuals |
| `docs/QUICKSTART_IOT_GATEWAY.md` | 3-step quick start |
| `docs/IOT_GATEWAY_README.md` | Full technical documentation |
| `docs/ARCHITECTURE_FLOW.md` | System flow diagrams |
| `docs/DATABASE_SCHEMA.md` | All 11 database tables |
| `docs/TABLES_REFERENCE.md` | Quick table reference |
| `docs/CHANGES_SUMMARY.md` | What was created/modified |

## ✨ What's Organized

### ✅ Scripts Moved to `scripts/`
- All `.sh` files are now in `scripts/` folder
- Makes root directory cleaner
- Easy to find and manage startup/stop scripts

### ✅ Documentation Moved to `docs/`
- All `.md` files are now in `docs/` folder  
- Comprehensive documentation in one place
- Easy to navigate and read

### ✅ Clean Root Directory
- Only essential files in root
- Main README as entry point
- Easy to understand project structure

## 🎯 File Locations Quick Reference

```bash
# Start gateway and sensors
./scripts/start_iot_gateway.sh

# Read complete guide
cat docs/README_COMPLETE.md

# Setup database
psql -U postgres -d mapek_dt -f setup_complete_database.sql

# Run tests
python3 test_system.py

# Check gateway
python3 iot_gateway.py
```

## 📦 Project Components

- **Gateway:** `iot_gateway.py` (port 3043)
- **Sensors:** `iot_scripts/*.py` (ports 8001-8004)
- **MAPE-K:** `plain_mapek/*.py`
- **Database:** `setup_complete_database.sql`
- **Tests:** `test_system.py`
- **Scripts:** `scripts/*.sh`
- **Docs:** `docs/*.md`

---

**Everything is organized and ready to use! 🚀**

Start with `README.md` in the root directory.
