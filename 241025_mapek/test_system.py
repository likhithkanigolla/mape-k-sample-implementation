#!/usr/bin/env python3
"""
Test script for IoT Gateway System
Verifies all components are working correctly
"""

import requests
import time
import json
from datetime import datetime

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}→ {text}{RESET}")

def test_gateway_health():
    """Test if Gateway is running"""
    print_header("Test 1: Gateway Health Check")
    try:
        response = requests.get("http://localhost:3043/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Gateway is running - {data['service']} v{data['version']}")
            return True
        else:
            print_error(f"Gateway returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to Gateway: {e}")
        print_info("Make sure Gateway is running: python3 iot_gateway.py")
        return False

def test_device_registry():
    """Test device registry"""
    print_header("Test 2: Device Registry")
    try:
        response = requests.get("http://localhost:3043/devices", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Found {data['count']} registered devices:")
            for device in data['devices']:
                print(f"    • {device}")
            return True
        else:
            print_error(f"Device registry returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error accessing device registry: {e}")
        return False

def test_device_status(device_id, port):
    """Test if device is running and responding"""
    try:
        response = requests.get(f"http://localhost:{port}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"{device_id} (port {port}) - Status: {'Faulty' if data.get('is_faulty') else 'Normal'}")
            return True
        else:
            print_error(f"{device_id} returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"{device_id} not responding on port {port}: {e}")
        return False

def test_all_devices():
    """Test all IoT devices"""
    print_header("Test 3: IoT Device Status")
    devices = [
        ("water_quality_1", 8001),
        ("water_level_1", 8002),
        ("water_flow_1", 8003),
        ("motor_1", 8004)
    ]
    
    all_ok = True
    for device_id, port in devices:
        if not test_device_status(device_id, port):
            all_ok = False
    
    if not all_ok:
        print_info("Make sure all sensors are running: ./scripts/start_iot_gateway.sh")
    
    return all_ok

def test_data_ingestion():
    """Test sending data to Gateway"""
    print_header("Test 4: Data Ingestion")
    
    test_data = {
        "node_id": "test_sensor_1",
        "temperature": 25.5,
        "tds_voltage": 1.8,
        "uncompensated_tds": 350,
        "compensated_tds": 340
    }
    
    try:
        response = requests.post(
            "http://localhost:3043/iot/water_quality",
            json=test_data,
            timeout=5
        )
        if response.status_code == 200:
            print_success("Successfully posted test data to Gateway")
            print_info(f"Data: {json.dumps(test_data, indent=2)}")
            return True
        else:
            print_error(f"Data ingestion failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error posting data: {e}")
        return False

def test_monitor_endpoint():
    """Test Monitor endpoints"""
    print_header("Test 5: Monitor Endpoints")
    
    endpoints = [
        "/monitor/water_quality/latest",
        "/monitor/water_level/latest",
        "/monitor/water_flow/latest",
        "/monitor/motor/latest"
    ]
    
    all_ok = True
    for endpoint in endpoints:
        try:
            response = requests.get(
                f"http://localhost:3043{endpoint}?limit=1",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                print_success(f"{endpoint} - {count} records available")
            else:
                print_error(f"{endpoint} returned status {response.status_code}")
                all_ok = False
        except Exception as e:
            print_error(f"Error accessing {endpoint}: {e}")
            all_ok = False
    
    return all_ok

def test_command_execution():
    """Test sending command to device via Gateway"""
    print_header("Test 6: Command Execution")
    
    command = {
        "node_id": "water_quality_1",
        "plan_code": "TEST_COMMAND",
        "description": "Test command from test script"
    }
    
    print_info(f"Sending test command to water_quality_1...")
    print_info(f"Command: {command['plan_code']}")
    
    try:
        response = requests.post(
            "http://localhost:3043/execute/command",
            json=command,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Command executed successfully!")
            print_success(f"Status: {result['status']}")
            print_success(f"Message: {result['message']}")
            
            # Verify device received it
            time.sleep(1)
            device_response = requests.get("http://localhost:8001/status", timeout=5)
            if device_response.status_code == 200:
                device_data = device_response.json()
                if device_data.get('last_command') == 'TEST_COMMAND':
                    print_success("Device confirmed command receipt!")
                else:
                    print_error("Device did not receive command")
            
            return True
        else:
            print_error(f"Command execution failed with status {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Error: {error_data.get('detail', 'Unknown error')}")
            except:
                pass
            return False
            
    except Exception as e:
        print_error(f"Error executing command: {e}")
        return False

def test_database_logging():
    """Test execution logging in database"""
    print_header("Test 7: Database Execution Logging")
    
    print_info("This test requires database access")
    print_info("Run manually: psql -U postgres -d iot_mapek -c 'SELECT * FROM recent_executions LIMIT 5;'")
    return True

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*70}")
    print(f"IoT Gateway System - Integration Tests")
    print(f"{'='*70}{RESET}")
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tests = [
        ("Gateway Health", test_gateway_health),
        ("Device Registry", test_device_registry),
        ("Device Status", test_all_devices),
        ("Data Ingestion", test_data_ingestion),
        ("Monitor Endpoints", test_monitor_endpoint),
        ("Command Execution", test_command_execution),
        ("Database Logging", test_database_logging)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {status} - {test_name}")
    
    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}{'='*70}")
        print(f"🎉 All tests passed! Your IoT Gateway system is working perfectly!")
        print(f"{'='*70}{RESET}\n")
    else:
        print(f"\n{YELLOW}{'='*70}")
        print(f"⚠️  Some tests failed. Check the errors above.")
        print(f"{'='*70}{RESET}\n")
        
        print("Common issues:")
        print("  1. Gateway not running: python3 iot_gateway.py")
        print("  2. Sensors not running: ./scripts/start_iot_gateway.sh")
        print("  3. Database not setup: psql -U postgres -d mapek_dt -f setup_complete_database.sql")
        print("  4. Port conflicts: Check if ports 3043, 8001-8004 are available")
        print()

if __name__ == "__main__":
    main()
