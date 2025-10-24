#!/bin/bash

# Stop script for Plain MAPE-K System
# This script stops all components of the plain MAPE-K system

echo "======================================"
echo "Stopping Plain MAPE-K System"
echo "======================================"
echo ""

# Function to kill processes by script name
kill_processes() {
    local pattern=$1
    local name=$2
    
    pids=$(ps aux | grep "$pattern" | grep -v grep | awk '{print $2}')
    
    if [ -n "$pids" ]; then
        echo "Stopping $name..."
        echo "$pids" | xargs kill -15 2>/dev/null
        sleep 1
        # Force kill if still running
        echo "$pids" | xargs kill -9 2>/dev/null
        echo "  ✓ Stopped"
    else
        echo "No running $name found"
    fi
}

# Stop all components
kill_processes "water_quality_sensor.py" "Water Quality Sensor"
kill_processes "water_flow_sensor.py" "Water Flow Sensor"
kill_processes "water_level_sensor.py" "Water Level Sensor"
kill_processes "motor_sensor.py" "Motor Sensor"
kill_processes "plain_mapek/main.py" "MAPE-K Loop"

echo ""
echo "======================================"
echo "✅ All components stopped"
echo "======================================"
echo ""
