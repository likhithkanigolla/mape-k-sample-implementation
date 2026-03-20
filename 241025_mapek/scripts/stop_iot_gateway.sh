#!/bin/bash

# Stop IoT Gateway and All Sensor Scripts

echo "======================================================================"
echo "Stopping IoT Gateway System"
echo "======================================================================"

if [ ! -f .iot_pids ]; then
    echo "Error: PID file not found. Services may not be running."
    echo "Trying to stop by port..."
    
    # Kill processes by port
    lsof -ti:3043 | xargs kill -9 2>/dev/null
    lsof -ti:8001 | xargs kill -9 2>/dev/null
    lsof -ti:8002 | xargs kill -9 2>/dev/null
    lsof -ti:8003 | xargs kill -9 2>/dev/null
    lsof -ti:8004 | xargs kill -9 2>/dev/null
    
    echo "Stopped processes on ports 3043, 8001-8004"
    exit 0
fi

# Read PIDs from file
PIDS=$(cat .iot_pids)

echo "Stopping services..."
for PID in $PIDS; do
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null
        echo "  ✓ Stopped process $PID"
    else
        echo "  • Process $PID not running"
    fi
done

# Clean up PID file
rm -f .iot_pids

# Extra cleanup - kill any remaining processes on the ports
lsof -ti:3043 | xargs kill -9 2>/dev/null
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null
lsof -ti:8003 | xargs kill -9 2>/dev/null
lsof -ti:8004 | xargs kill -9 2>/dev/null

echo ""
echo "======================================================================"
echo "All IoT services stopped"
echo "======================================================================"
