#!/bin/bash

# Startup script for Plain MAPE-K System
# This script helps start all components of the plain MAPE-K system

echo "======================================"
echo "Plain MAPE-K System Startup"
echo "======================================"
echo ""

# Check if running from correct directory
if [ ! -d "plain_mapek" ] || [ ! -d "iot_scripts" ]; then
    echo "❌ Error: Please run this script from the 241025_mapek directory"
    exit 1
fi

# Create logs directory
mkdir -p logs

echo "📋 Starting Plain MAPE-K System Components"
echo ""
echo "This will start:"
echo "  1. IoT Sensor Simulators (4 sensors)"
echo "  2. MAPE-K Loop"
echo ""
echo "Note: Make sure PostgreSQL and FastAPI server are running first!"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."
echo ""

# Function to start a component in background
start_component() {
    local name=$1
    local script=$2
    local log=$3
    
    echo "Starting $name..."
    nohup python3 "$script" > "$log" 2>&1 &
    echo "  → PID: $!"
}

# Start IoT Sensors
echo "🌊 Starting IoT Sensors..."
start_component "Water Quality Sensor" "iot_scripts/water_quality_sensor.py" "logs/water_quality.log"
start_component "Water Flow Sensor" "iot_scripts/water_flow_sensor.py" "logs/water_flow.log"
start_component "Water Level Sensor" "iot_scripts/water_level_sensor.py" "logs/water_level.log"
start_component "Motor Sensor" "iot_scripts/motor_sensor.py" "logs/motor.log"
echo ""

# Wait a bit for sensors to initialize
echo "⏳ Waiting 5 seconds for sensors to initialize..."
sleep 5
echo ""

# Start MAPE-K Loop
echo "🔄 Starting MAPE-K Loop..."
start_component "MAPE-K Loop" "plain_mapek/main.py" "logs/mapek_output.log"
echo ""

echo "======================================"
echo "✅ All components started!"
echo "======================================"
echo ""
echo "To monitor the system:"
echo "  • MAPE-K logs:  tail -f logs/plain_mapek.log"
echo "  • Sensor logs:  tail -f logs/water_quality.log"
echo "  • All output:   tail -f logs/*.log"
echo ""
echo "To stop all components:"
echo "  ./stop_all.sh"
echo ""
echo "Process IDs saved. Check 'ps aux | grep python' to see running processes"
echo ""
