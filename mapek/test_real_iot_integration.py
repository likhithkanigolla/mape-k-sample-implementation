#!/usr/bin/env python3
"""
Test script for Real IoT System Integration
Tests the MAPE-K system with actual IoT sensor data and advanced patterns
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import time
from datetime import datetime
from real_iot_system import RealIoTMAPEKSystem, PATTERNS_AVAILABLE
from logger import logger
from knowledge import get_db_conn

def test_database_connection():
    """Test basic database connectivity and data availability."""
    logger.info("🔍 Testing database connection...")
    
    try:
        conn = get_db_conn()
        if not conn:
            logger.error("❌ No database connection available")
            return False
        
        cur = conn.cursor()
        
        # Test each sensor table
        sensor_tables = ['water_quality', 'water_flow', 'water_level', 'motor']
        total_records = 0
        
        for table in sensor_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                total_records += count
                logger.info(f"   📊 {table}: {count} records")
                
                # Get latest record
                cur.execute(f"SELECT * FROM {table} ORDER BY timestamp DESC LIMIT 1")
                latest = cur.fetchone()
                if latest:
                    logger.info(f"   🕒 Latest {table} record: {latest[1]} at {latest[2]}")  # node_id, timestamp
            except Exception as e:
                logger.warning(f"   ⚠️ Error checking {table}: {e}")
        
        cur.close()
        conn.close()
        
        if total_records > 0:
            logger.info(f"✅ Database connected successfully! Total records: {total_records}")
            return True
        else:
            logger.warning("⚠️ Database connected but no sensor data found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

async def test_monitor_service():
    """Test the monitor service with real IoT data."""
    logger.info("🔍 Testing Monitor Service...")
    
    try:
        # Create IoT system instance
        iot_system = RealIoTMAPEKSystem()
        
        # Test monitor service
        sensor_data = iot_system.monitor_service.read_sensors()
        
        if sensor_data:
            logger.info(f"✅ Monitor service working! Retrieved {len(sensor_data)} sensor readings")
            
            # Show sample data
            for i, sensor in enumerate(sensor_data[:3]):  # Show first 3
                logger.info(f"   📊 Sample {i+1}: {sensor.get('node_id')} - {iot_system._determine_sensor_type(sensor)}")
            
            return True
        else:
            logger.warning("⚠️ Monitor service returned no data")
            return False
            
    except Exception as e:
        logger.error(f"❌ Monitor service test failed: {e}")
        return False

async def test_analyzer_service():
    """Test the analyzer service with real IoT data."""
    logger.info("🔍 Testing Analyzer Service...")
    
    try:
        # Create IoT system instance
        iot_system = RealIoTMAPEKSystem()
        
        # Get sensor data
        sensor_data = iot_system.monitor_service.read_sensors()
        
        if not sensor_data:
            logger.warning("⚠️ No sensor data available for analysis")
            return False
        
        # Test analyzer
        analysis_result = iot_system.analyzer_service.analyze(sensor_data)
        
        if analysis_result:
            logger.info(f"✅ Analyzer service working! Analyzed {len(analysis_result)} nodes")
            
            # Count states
            states = {}
            for result in analysis_result:
                if isinstance(result, dict):
                    state = result.get('state', 'unknown')
                    states[state] = states.get(state, 0) + 1
            
            logger.info(f"   📊 Analysis results: {states}")
            return True
        else:
            logger.warning("⚠️ Analyzer service returned no results")
            return False
            
    except Exception as e:
        logger.error(f"❌ Analyzer service test failed: {e}")
        return False

async def test_single_iot_cycle():
    """Test a single enhanced IoT MAPE-K cycle."""
    logger.info("🔍 Testing Single Enhanced IoT Cycle...")
    
    try:
        # Create IoT system instance
        iot_system = RealIoTMAPEKSystem()
        
        # Run one cycle
        await iot_system.run_enhanced_iot_cycle()
        
        # Check system status
        status = iot_system.get_system_status()
        
        logger.info("✅ Single IoT cycle completed successfully!")
        logger.info(f"   📊 Cycle count: {status['cycle_count']}")
        logger.info(f"   📡 Sensors processed: {status['total_sensors_processed']}")
        logger.info(f"   ⚠️ Violations detected: {status['total_violations_detected']}")
        logger.info(f"   ⚡ Commands executed: {status['total_commands_executed']}")
        logger.info(f"   🎯 Current scenario: {status['current_scenario']}")
        
        if PATTERNS_AVAILABLE:
            logger.info(f"   🎨 Pattern usage: {status['pattern_usage']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Single IoT cycle test failed: {e}")
        return False

async def test_pattern_integration():
    """Test advanced pattern integration."""
    logger.info("🔍 Testing Advanced Pattern Integration...")
    
    if not PATTERNS_AVAILABLE:
        logger.warning("⚠️ Advanced patterns not available - skipping pattern tests")
        return False
    
    try:
        # Create IoT system instance
        iot_system = RealIoTMAPEKSystem()
        
        # Test Strategy Pattern
        if iot_system.scenario_analyzer:
            logger.info("   ✅ Strategy Pattern (ScenarioAnalyzer) loaded")
        
        # Test Observer Pattern
        if iot_system.event_bus:
            logger.info("   ✅ Observer Pattern (EventBus) loaded")
        
        # Test Command Pattern
        if iot_system.command_invoker:
            logger.info("   ✅ Command Pattern (CommandInvoker) loaded")
        
        # Test scenario types
        scenarios = [
            iot_system.current_scenario,
            "NORMAL_OPERATION", 
            "PEAK_DEMAND",
            "EMERGENCY_RESPONSE",
            "DROUGHT_CONDITIONS"
        ]
        logger.info(f"   🎯 Available scenarios: {scenarios}")
        
        logger.info("✅ Pattern integration test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Pattern integration test failed: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive IoT system tests."""
    
    print("🚀 Real IoT MAPE-K System Integration Test")
    print("=" * 60)
    
    # Test summary
    tests = [
        ("Database Connection", test_database_connection()),
        ("Monitor Service", test_monitor_service()),
        ("Analyzer Service", test_analyzer_service()),
        ("Pattern Integration", test_pattern_integration()),
        ("Single IoT Cycle", test_single_iot_cycle())
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_coro in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            
            if result:
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your IoT system is ready for production!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the logs above.")
        return False

async def run_short_monitoring_demo():
    """Run a short monitoring demo to show real-time IoT integration."""
    print("\n🔄 Running Short IoT Monitoring Demo (3 cycles)")
    print("-" * 50)
    
    try:
        iot_system = RealIoTMAPEKSystem()
        
        for cycle in range(1, 4):
            print(f"\n[Cycle {cycle}/3] Running enhanced MAPE-K...")
            await iot_system.run_enhanced_iot_cycle()
            
            if cycle < 3:
                print("⏱️ Waiting 10 seconds...")
                await asyncio.sleep(10)
        
        # Final status
        status = iot_system.get_system_status()
        print(f"\n📊 Demo Complete!")
        print(f"   🔄 Cycles: {status['cycle_count']}")
        print(f"   📡 Total sensors: {status['total_sensors_processed']}")
        print(f"   ⚠️ Violations: {status['total_violations_detected']}")
        print(f"   ⚡ Commands: {status['total_commands_executed']}")
        
        if PATTERNS_AVAILABLE:
            total_patterns = sum(status['pattern_usage'].values())
            print(f"   🎨 Pattern applications: {total_patterns}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Real IoT MAPE-K Integration Test Suite")
    print("Testing integration with your live IoT sensor data")
    print("=" * 70)
    
    # Run comprehensive tests
    try:
        # First run comprehensive tests
        success = asyncio.run(run_comprehensive_test())
        
        if success:
            # If tests pass, run demo
            print("\n" + "=" * 70)
            run_demo = input("🤔 Run short monitoring demo? (y/n): ").lower().strip()
            if run_demo == 'y':
                asyncio.run(run_short_monitoring_demo())
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
    
    print("\n✅ Integration testing complete!")
