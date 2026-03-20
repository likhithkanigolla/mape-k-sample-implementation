#!/bin/bash

# Start IoT Gateway and All Sensor Scripts
# This script starts all components of the IoT system

echo "======================================================================"
echo "Starting IoT Gateway System"
echo "======================================================================"

# Prevent duplicate process sets on repeated starts.
if [ -f .iot_pids ]; then
    echo "Existing PID file detected. Cleaning up previous IoT processes..."
    ./scripts/stop_iot_gateway.sh >/dev/null 2>&1 || true
fi

# Extra safety: clear processes that may not be tracked by PID file.
for PORT in 3043 8001 8002 8003 8004; do
    pids=$(lsof -ti:$PORT 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "Releasing port $PORT from stale process(es): $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
    fi
done

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if FastAPI and uvicorn are installed
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "Error: FastAPI and uvicorn are required"
    echo "Install with: pip install fastapi uvicorn psycopg2-binary requests pydantic"
    exit 1
fi

echo -e "${BLUE}Step 1:${NC} Starting IoT Gateway on port 3043..."
python3 iot_gateway.py &
GATEWAY_PID=$!
echo -e "${GREEN}✓${NC} Gateway started (PID: $GATEWAY_PID)"
sleep 3

echo -e "\n${BLUE}Step 2:${NC} Starting IoT Sensor Scripts..."

echo "  Starting Water Quality Sensor (port 8001)..."
python3 iot_scripts/water_quality_sensor.py &
WQ_PID=$!
echo -e "  ${GREEN}✓${NC} Water Quality Sensor started (PID: $WQ_PID)"
sleep 1

echo "  Starting Water Level Sensor (port 8002)..."
python3 iot_scripts/water_level_sensor.py &
WL_PID=$!
echo -e "  ${GREEN}✓${NC} Water Level Sensor started (PID: $WL_PID)"
sleep 1

echo "  Starting Water Flow Sensor (port 8003)..."
python3 iot_scripts/water_flow_sensor.py &
WF_PID=$!
echo -e "  ${GREEN}✓${NC} Water Flow Sensor started (PID: $WF_PID)"
sleep 1

echo "  Starting Motor Sensor (port 8004)..."
python3 iot_scripts/motor_sensor.py &
MOTOR_PID=$!
echo -e "  ${GREEN}✓${NC} Motor Sensor started (PID: $MOTOR_PID)"
sleep 1

echo -e "\n======================================================================"
echo -e "${GREEN}All components started successfully!${NC}"
echo "======================================================================"
echo ""
echo "Services running:"
echo "  • IoT Gateway:          http://localhost:3043"
echo "  • Water Quality Sensor: http://localhost:8001"
echo "  • Water Level Sensor:   http://localhost:8002"
echo "  • Water Flow Sensor:    http://localhost:8003"
echo "  • Motor Sensor:         http://localhost:8004"
echo ""
echo "PIDs saved to: .iot_pids"
echo ""
echo "To start MAPE-K loop:"
echo "  cd plain_mapek && python3 main.py"
echo ""
echo "To stop all services:"
echo "  ./stop_iot_gateway.sh"
echo ""
echo "Press Ctrl+C to view logs (services will continue running)"
echo "======================================================================"

# Save PIDs to file for stop script
echo "$GATEWAY_PID" > .iot_pids
echo "$WQ_PID" >> .iot_pids
echo "$WL_PID" >> .iot_pids
echo "$WF_PID" >> .iot_pids
echo "$MOTOR_PID" >> .iot_pids

# Wait for user interrupt
wait
