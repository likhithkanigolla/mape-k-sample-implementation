"""
Adapter Pattern Implementation for Legacy System Integration
Enables seamless integration between modern MAPE-K architecture and legacy water utility systems.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Protocol
from enum import Enum
from dataclasses import dataclass
import asyncio
import logging
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import struct
import socket

logger = logging.getLogger(__name__)


class LegacySystemType(Enum):
    """Types of legacy systems that can be integrated."""
    SCADA_MODBUS = "scada_modbus"
    OPC_UA = "opc_ua"
    DCS_PROPRIETARY = "dcs_proprietary"
    HISTORIAN_PI = "historian_pi"
    XML_WEB_SERVICE = "xml_web_service"
    CSV_FILE_SYSTEM = "csv_file_system"
    SERIAL_PROTOCOL = "serial_protocol"
    MQTT_LEGACY = "mqtt_legacy"


@dataclass
class SensorReading:
    """Standardized sensor reading format for the modern system."""
    sensor_id: str
    value: float
    timestamp: datetime
    sensor_type: str
    quality: str = "good"
    unit: str = "unknown"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "sensor_id": self.sensor_id,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "sensor_type": self.sensor_type,
            "quality": self.quality,
            "unit": self.unit,
            "metadata": self.metadata
        }


@dataclass
class ControlCommand:
    """Standardized control command format for the modern system."""
    target_id: str
    command_type: str
    value: float
    timestamp: datetime
    priority: int = 1
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ModernSystemInterface(Protocol):
    """Interface that modern MAPE-K system expects."""
    
    async def read_sensors(self) -> List[SensorReading]:
        """Read all sensor data."""
        ...
    
    async def write_control_command(self, command: ControlCommand) -> bool:
        """Execute a control command."""
        ...
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        ...


class LegacySystemInterface(ABC):
    """Abstract interface for legacy systems."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to legacy system."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from legacy system."""
        pass
    
    @abstractmethod
    async def read_raw_data(self) -> Dict[str, Any]:
        """Read raw data from legacy system."""
        pass
    
    @abstractmethod
    async def write_raw_command(self, command_data: Dict[str, Any]) -> bool:
        """Write raw command to legacy system."""
        pass
    
    @abstractmethod
    def get_system_info(self) -> Dict[str, str]:
        """Get information about the legacy system."""
        pass


class SCADAModbusSystem(LegacySystemInterface):
    """Legacy SCADA system using Modbus protocol."""
    
    def __init__(self, host: str, port: int, unit_id: int = 1):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.connected = False
        self.socket = None
        self.register_map = {
            # Modbus register mapping for different sensors
            "pressure_01": {"address": 40001, "multiplier": 0.1},
            "flow_01": {"address": 40002, "multiplier": 1.0},
            "temperature_01": {"address": 40003, "multiplier": 0.1},
            "valve_01": {"address": 40010, "multiplier": 1.0},
        }
    
    async def connect(self) -> bool:
        """Connect to SCADA Modbus system."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.connect, (self.host, self.port)
            )
            self.connected = True
            logger.info(f"Connected to SCADA Modbus at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SCADA Modbus: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from SCADA system."""
        if self.socket:
            self.socket.close()
            self.connected = False
            logger.info("Disconnected from SCADA Modbus")
    
    async def read_raw_data(self) -> Dict[str, Any]:
        """Read raw Modbus data."""
        if not self.connected:
            raise ConnectionError("Not connected to SCADA system")
        
        raw_data = {}
        
        # Simulate Modbus register reads
        for sensor_id, config in self.register_map.items():
            try:
                # Simulate Modbus read holding register
                raw_value = await self._read_modbus_register(config["address"])
                actual_value = raw_value * config["multiplier"]
                
                raw_data[sensor_id] = {
                    "raw_value": raw_value,
                    "actual_value": actual_value,
                    "register": config["address"],
                    "timestamp": datetime.now().isoformat(),
                    "quality": "good" if raw_value is not None else "bad"
                }
            except Exception as e:
                logger.error(f"Failed to read {sensor_id}: {e}")
                raw_data[sensor_id] = {
                    "raw_value": None,
                    "actual_value": None,
                    "register": config["address"],
                    "timestamp": datetime.now().isoformat(),
                    "quality": "bad",
                    "error": str(e)
                }
        
        return raw_data
    
    async def write_raw_command(self, command_data: Dict[str, Any]) -> bool:
        """Write command to SCADA system via Modbus."""
        if not self.connected:
            raise ConnectionError("Not connected to SCADA system")
        
        try:
            target = command_data.get("target")
            value = command_data.get("value")
            
            if target in self.register_map:
                register_addr = self.register_map[target]["address"]
                multiplier = self.register_map[target]["multiplier"]
                raw_value = int(value / multiplier)
                
                success = await self._write_modbus_register(register_addr, raw_value)
                
                if success:
                    logger.info(f"Successfully wrote {value} to {target} (register {register_addr})")
                    return True
                else:
                    logger.error(f"Failed to write to {target}")
                    return False
            else:
                logger.error(f"Unknown target: {target}")
                return False
                
        except Exception as e:
            logger.error(f"Error writing command: {e}")
            return False
    
    def get_system_info(self) -> Dict[str, str]:
        """Get SCADA system information."""
        return {
            "system_type": "SCADA Modbus",
            "host": self.host,
            "port": str(self.port),
            "unit_id": str(self.unit_id),
            "protocol_version": "Modbus TCP",
            "vendor": "Generic SCADA",
            "connected": str(self.connected)
        }
    
    async def _read_modbus_register(self, address: int) -> Optional[int]:
        """Simulate Modbus register read."""
        # In real implementation, this would use a Modbus library
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Simulate different sensor values based on address
        simulation_values = {
            40001: 250,  # Pressure (25.0 bar after multiplier)
            40002: 45,   # Flow (45.0 L/min)
            40003: 220,  # Temperature (22.0°C after multiplier)
            40010: 75,   # Valve position (75%)
        }
        
        return simulation_values.get(address, 0)
    
    async def _write_modbus_register(self, address: int, value: int) -> bool:
        """Simulate Modbus register write."""
        # In real implementation, this would use a Modbus library
        await asyncio.sleep(0.1)  # Simulate network delay
        logger.debug(f"Writing value {value} to Modbus register {address}")
        return True  # Simulate successful write


class XMLWebServiceSystem(LegacySystemInterface):
    """Legacy system using XML web services (SOAP-like)."""
    
    def __init__(self, endpoint_url: str, username: str, password: str):
        self.endpoint_url = endpoint_url
        self.username = username
        self.password = password
        self.session_token = None
        self.connected = False
    
    async def connect(self) -> bool:
        """Authenticate with XML web service."""
        try:
            # Simulate authentication
            auth_xml = f"""
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <authenticate>
                        <username>{self.username}</username>
                        <password>{self.password}</password>
                    </authenticate>
                </soap:Body>
            </soap:Envelope>
            """
            
            # Simulate HTTP POST to web service
            await asyncio.sleep(0.2)  # Simulate network call
            self.session_token = "mock_session_token_12345"
            self.connected = True
            
            logger.info(f"Connected to XML Web Service at {self.endpoint_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to XML Web Service: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from web service."""
        self.session_token = None
        self.connected = False
        logger.info("Disconnected from XML Web Service")
    
    async def read_raw_data(self) -> Dict[str, Any]:
        """Read data via XML web service."""
        if not self.connected:
            raise ConnectionError("Not connected to XML Web Service")
        
        # Simulate SOAP request for sensor data
        request_xml = f"""
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Header>
                <sessionToken>{self.session_token}</sessionToken>
            </soap:Header>
            <soap:Body>
                <getSensorData>
                    <timestamp>{datetime.now().isoformat()}</timestamp>
                </getSensorData>
            </soap:Body>
        </soap:Envelope>
        """
        
        # Simulate web service call
        await asyncio.sleep(0.3)  # Simulate network delay
        
        # Simulate XML response
        response_xml = """
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <getSensorDataResponse>
                    <sensors>
                        <sensor id="WQ_001" type="quality" value="7.2" unit="pH" timestamp="2024-08-10T12:00:00Z"/>
                        <sensor id="PR_001" type="pressure" value="3.1" unit="bar" timestamp="2024-08-10T12:00:00Z"/>
                        <sensor id="FL_001" type="flow" value="52.3" unit="L/min" timestamp="2024-08-10T12:00:00Z"/>
                    </sensors>
                </getSensorDataResponse>
            </soap:Body>
        </soap:Envelope>
        """
        
        # Parse XML response
        return self._parse_xml_sensor_data(response_xml)
    
    async def write_raw_command(self, command_data: Dict[str, Any]) -> bool:
        """Send command via XML web service."""
        if not self.connected:
            raise ConnectionError("Not connected to XML Web Service")
        
        target = command_data.get("target")
        value = command_data.get("value")
        command_type = command_data.get("command_type", "set_value")
        
        command_xml = f"""
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Header>
                <sessionToken>{self.session_token}</sessionToken>
            </soap:Header>
            <soap:Body>
                <executeCommand>
                    <target>{target}</target>
                    <commandType>{command_type}</commandType>
                    <value>{value}</value>
                    <timestamp>{datetime.now().isoformat()}</timestamp>
                </executeCommand>
            </soap:Body>
        </soap:Envelope>
        """
        
        # Simulate web service call
        await asyncio.sleep(0.2)  # Simulate network delay
        
        logger.info(f"Sent command to {target}: {command_type}={value}")
        return True  # Simulate successful command
    
    def get_system_info(self) -> Dict[str, str]:
        """Get web service system information."""
        return {
            "system_type": "XML Web Service",
            "endpoint": self.endpoint_url,
            "protocol": "SOAP/HTTP",
            "authentication": "username/password",
            "connected": str(self.connected),
            "session_active": str(self.session_token is not None)
        }
    
    def _parse_xml_sensor_data(self, xml_data: str) -> Dict[str, Any]:
        """Parse XML sensor data response."""
        try:
            root = ET.fromstring(xml_data)
            sensors_data = {}
            
            # Find sensor elements (simplified XPath)
            for sensor in root.iter():
                if sensor.tag == "sensor":
                    sensor_id = sensor.get("id")
                    sensors_data[sensor_id] = {
                        "sensor_type": sensor.get("type"),
                        "value": float(sensor.get("value")),
                        "unit": sensor.get("unit"),
                        "timestamp": sensor.get("timestamp"),
                        "quality": "good"
                    }
            
            return sensors_data
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML sensor data: {e}")
            return {}


class CSVFileSystem(LegacySystemInterface):
    """Legacy system that uses CSV files for data exchange."""
    
    def __init__(self, input_file_path: str, output_file_path: str):
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path
        self.connected = False
        self.last_read_time = None
    
    async def connect(self) -> bool:
        """Check if CSV files are accessible."""
        try:
            # Check if input file exists and is readable
            with open(self.input_file_path, 'r') as f:
                f.readline()  # Try to read first line
            
            # Check if output file is writable
            with open(self.output_file_path, 'a') as f:
                pass  # Just test write access
            
            self.connected = True
            logger.info(f"Connected to CSV file system: {self.input_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to CSV file system: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from file system."""
        self.connected = False
        logger.info("Disconnected from CSV file system")
    
    async def read_raw_data(self) -> Dict[str, Any]:
        """Read data from CSV file."""
        if not self.connected:
            raise ConnectionError("Not connected to CSV file system")
        
        try:
            # Read CSV file asynchronously
            import aiofiles
            async with aiofiles.open(self.input_file_path, 'r') as f:
                lines = await f.readlines()
            
            # Parse CSV data (assuming first line is header)
            if len(lines) < 2:
                return {}
            
            headers = lines[0].strip().split(',')
            latest_data_line = lines[-1].strip().split(',')  # Get latest reading
            
            csv_data = {}
            for i, header in enumerate(headers):
                if i < len(latest_data_line):
                    try:
                        # Try to parse as float, fallback to string
                        value = float(latest_data_line[i])
                    except ValueError:
                        value = latest_data_line[i]
                    
                    csv_data[header] = {
                        "value": value,
                        "timestamp": datetime.now().isoformat(),
                        "quality": "good",
                        "source": "csv_file"
                    }
            
            self.last_read_time = datetime.now()
            return csv_data
            
        except Exception as e:
            logger.error(f"Failed to read CSV data: {e}")
            return {}
    
    async def write_raw_command(self, command_data: Dict[str, Any]) -> bool:
        """Write command to CSV file."""
        if not self.connected:
            raise ConnectionError("Not connected to CSV file system")
        
        try:
            # Append command to output CSV file
            import aiofiles
            async with aiofiles.open(self.output_file_path, 'a') as f:
                timestamp = datetime.now().isoformat()
                target = command_data.get("target", "unknown")
                command_type = command_data.get("command_type", "set")
                value = command_data.get("value", 0)
                
                csv_line = f"{timestamp},{target},{command_type},{value}\n"
                await f.write(csv_line)
            
            logger.info(f"Wrote command to CSV: {command_data}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write CSV command: {e}")
            return False
    
    def get_system_info(self) -> Dict[str, str]:
        """Get CSV file system information."""
        return {
            "system_type": "CSV File System",
            "input_file": self.input_file_path,
            "output_file": self.output_file_path,
            "connected": str(self.connected),
            "last_read": self.last_read_time.isoformat() if self.last_read_time else "never"
        }


class LegacySystemAdapter:
    """Adapter that converts legacy system interface to modern system interface."""
    
    def __init__(self, legacy_system: LegacySystemInterface, 
                 sensor_mapping: Dict[str, Dict[str, Any]],
                 command_mapping: Dict[str, Dict[str, Any]]):
        self.legacy_system = legacy_system
        self.sensor_mapping = sensor_mapping  # Maps legacy sensor IDs to modern format
        self.command_mapping = command_mapping  # Maps modern commands to legacy format
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to the legacy system."""
        self.connected = await self.legacy_system.connect()
        return self.connected
    
    async def disconnect(self) -> None:
        """Disconnect from the legacy system."""
        await self.legacy_system.disconnect()
        self.connected = False
    
    async def read_sensors(self) -> List[SensorReading]:
        """Read sensors and convert to modern format."""
        if not self.connected:
            raise ConnectionError("Adapter not connected to legacy system")
        
        # Get raw data from legacy system
        raw_data = await self.legacy_system.read_raw_data()
        
        # Convert to modern sensor readings
        sensor_readings = []
        
        for legacy_id, raw_sensor_data in raw_data.items():
            if legacy_id in self.sensor_mapping:
                mapping = self.sensor_mapping[legacy_id]
                
                # Extract and convert values
                value = raw_sensor_data.get("value") or raw_sensor_data.get("actual_value", 0.0)
                
                # Apply any conversion factors
                if "conversion_factor" in mapping:
                    value = value * mapping["conversion_factor"]
                
                # Convert timestamp
                timestamp_str = raw_sensor_data.get("timestamp")
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        timestamp = datetime.now()
                else:
                    timestamp = datetime.now()
                
                # Create standardized sensor reading
                sensor_reading = SensorReading(
                    sensor_id=mapping.get("modern_id", legacy_id),
                    value=float(value),
                    timestamp=timestamp,
                    sensor_type=mapping.get("sensor_type", "unknown"),
                    quality=raw_sensor_data.get("quality", "good"),
                    unit=mapping.get("unit", raw_sensor_data.get("unit", "unknown")),
                    metadata={
                        "legacy_id": legacy_id,
                        "legacy_system": self.legacy_system.get_system_info()["system_type"],
                        "raw_data": raw_sensor_data
                    }
                )
                
                sensor_readings.append(sensor_reading)
                
        logger.debug(f"Converted {len(sensor_readings)} sensor readings from legacy system")
        return sensor_readings
    
    async def write_control_command(self, command: ControlCommand) -> bool:
        """Convert modern command to legacy format and execute."""
        if not self.connected:
            raise ConnectionError("Adapter not connected to legacy system")
        
        # Find mapping for the target
        legacy_target = None
        command_config = None
        
        for modern_target, config in self.command_mapping.items():
            if modern_target == command.target_id:
                legacy_target = config.get("legacy_target")
                command_config = config
                break
        
        if not legacy_target or not command_config:
            logger.error(f"No mapping found for command target: {command.target_id}")
            return False
        
        # Convert command value
        legacy_value = command.value
        if "conversion_factor" in command_config:
            legacy_value = legacy_value * command_config["conversion_factor"]
        
        # Apply value constraints
        if "min_value" in command_config:
            legacy_value = max(legacy_value, command_config["min_value"])
        if "max_value" in command_config:
            legacy_value = min(legacy_value, command_config["max_value"])
        
        # Create legacy command format
        legacy_command = {
            "target": legacy_target,
            "command_type": command_config.get("legacy_command_type", command.command_type),
            "value": legacy_value,
            "timestamp": command.timestamp.isoformat(),
            "priority": command.priority
        }
        
        # Add any system-specific parameters
        if "additional_params" in command_config:
            legacy_command.update(command_config["additional_params"])
        
        # Execute command on legacy system
        success = await self.legacy_system.write_raw_command(legacy_command)
        
        if success:
            logger.info(f"Successfully executed command on legacy system: {command.target_id}")
        else:
            logger.error(f"Failed to execute command on legacy system: {command.target_id}")
        
        return success
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status including legacy system information."""
        legacy_info = self.legacy_system.get_system_info()
        
        return {
            "connected": self.connected,
            "legacy_system": legacy_info,
            "adapter_info": {
                "sensor_mappings": len(self.sensor_mapping),
                "command_mappings": len(self.command_mapping),
                "last_check": datetime.now().isoformat()
            }
        }


class AdapterFactory:
    """Factory for creating adapters for different legacy systems."""
    
    @staticmethod
    def create_scada_adapter(host: str, port: int) -> LegacySystemAdapter:
        """Create adapter for SCADA Modbus system."""
        legacy_system = SCADAModbusSystem(host, port)
        
        # Define sensor mappings
        sensor_mapping = {
            "pressure_01": {
                "modern_id": "PRESSURE_MAIN_INLET",
                "sensor_type": "pressure",
                "unit": "bar",
                "conversion_factor": 1.0
            },
            "flow_01": {
                "modern_id": "FLOW_MAIN_LINE",
                "sensor_type": "flow",
                "unit": "L/min",
                "conversion_factor": 1.0
            },
            "temperature_01": {
                "modern_id": "TEMP_MAIN_LINE",
                "sensor_type": "temperature",
                "unit": "celsius",
                "conversion_factor": 1.0
            }
        }
        
        # Define command mappings
        command_mapping = {
            "VALVE_MAIN_CONTROL": {
                "legacy_target": "valve_01",
                "legacy_command_type": "set_position",
                "conversion_factor": 1.0,
                "min_value": 0.0,
                "max_value": 100.0
            }
        }
        
        return LegacySystemAdapter(legacy_system, sensor_mapping, command_mapping)
    
    @staticmethod
    def create_xml_webservice_adapter(url: str, username: str, password: str) -> LegacySystemAdapter:
        """Create adapter for XML web service system."""
        legacy_system = XMLWebServiceSystem(url, username, password)
        
        # Define sensor mappings for XML web service
        sensor_mapping = {
            "WQ_001": {
                "modern_id": "QUALITY_MAIN_OUTLET",
                "sensor_type": "quality",
                "unit": "pH",
                "conversion_factor": 1.0
            },
            "PR_001": {
                "modern_id": "PRESSURE_MAIN_OUTLET",
                "sensor_type": "pressure",
                "unit": "bar",
                "conversion_factor": 1.0
            },
            "FL_001": {
                "modern_id": "FLOW_MAIN_OUTLET",
                "sensor_type": "flow",
                "unit": "L/min",
                "conversion_factor": 1.0
            }
        }
        
        # Define command mappings
        command_mapping = {
            "PUMP_MAIN_CONTROL": {
                "legacy_target": "PUMP_001",
                "legacy_command_type": "set_speed",
                "conversion_factor": 1.0,
                "min_value": 0.0,
                "max_value": 100.0,
                "additional_params": {
                    "safety_check": True,
                    "gradual_change": True
                }
            }
        }
        
        return LegacySystemAdapter(legacy_system, sensor_mapping, command_mapping)
    
    @staticmethod
    def create_csv_adapter(input_file: str, output_file: str) -> LegacySystemAdapter:
        """Create adapter for CSV file-based system."""
        legacy_system = CSVFileSystem(input_file, output_file)
        
        # Define sensor mappings for CSV system
        sensor_mapping = {
            "sensor_pressure": {
                "modern_id": "PRESSURE_CSV_01",
                "sensor_type": "pressure",
                "unit": "bar",
                "conversion_factor": 1.0
            },
            "sensor_flow": {
                "modern_id": "FLOW_CSV_01",
                "sensor_type": "flow",
                "unit": "L/min",
                "conversion_factor": 1.0
            },
            "sensor_quality": {
                "modern_id": "QUALITY_CSV_01",
                "sensor_type": "quality",
                "unit": "pH",
                "conversion_factor": 1.0
            }
        }
        
        # Define command mappings
        command_mapping = {
            "VALVE_CSV_CONTROL": {
                "legacy_target": "valve_control",
                "legacy_command_type": "adjust",
                "conversion_factor": 1.0,
                "min_value": 0.0,
                "max_value": 100.0
            }
        }
        
        return LegacySystemAdapter(legacy_system, sensor_mapping, command_mapping)


# Integration manager for multiple legacy systems
class MultiSystemIntegrationManager:
    """Manages integration with multiple legacy systems simultaneously."""
    
    def __init__(self):
        self.adapters: Dict[str, LegacySystemAdapter] = {}
        self.system_priorities: Dict[str, int] = {}  # Priority for conflicting data
    
    def add_system(self, system_name: str, adapter: LegacySystemAdapter, priority: int = 1) -> None:
        """Add a legacy system adapter."""
        self.adapters[system_name] = adapter
        self.system_priorities[system_name] = priority
        logger.info(f"Added legacy system: {system_name} with priority {priority}")
    
    async def connect_all_systems(self) -> Dict[str, bool]:
        """Connect to all legacy systems."""
        connection_results = {}
        
        for system_name, adapter in self.adapters.items():
            try:
                success = await adapter.connect()
                connection_results[system_name] = success
                logger.info(f"Connection to {system_name}: {'Success' if success else 'Failed'}")
            except Exception as e:
                connection_results[system_name] = False
                logger.error(f"Failed to connect to {system_name}: {e}")
        
        return connection_results
    
    async def read_all_sensors(self) -> List[SensorReading]:
        """Read sensors from all connected systems."""
        all_readings = []
        
        for system_name, adapter in self.adapters.items():
            try:
                readings = await adapter.read_sensors()
                
                # Add system identifier to metadata
                for reading in readings:
                    reading.metadata["source_system"] = system_name
                    reading.metadata["system_priority"] = self.system_priorities[system_name]
                
                all_readings.extend(readings)
                logger.debug(f"Read {len(readings)} sensors from {system_name}")
                
            except Exception as e:
                logger.error(f"Failed to read sensors from {system_name}: {e}")
        
        # Remove duplicates based on sensor_id, keeping highest priority
        unique_readings = self._deduplicate_sensor_readings(all_readings)
        
        return unique_readings
    
    async def execute_command_on_best_system(self, command: ControlCommand) -> bool:
        """Execute command on the most appropriate system."""
        # Find systems that can handle this command
        capable_systems = []
        
        for system_name, adapter in self.adapters.items():
            # Check if system can handle the command (simplified check)
            system_status = await adapter.get_system_status()
            if system_status.get("connected", False):
                capable_systems.append((system_name, adapter, self.system_priorities[system_name]))
        
        if not capable_systems:
            logger.error("No capable systems available for command execution")
            return False
        
        # Sort by priority (highest first)
        capable_systems.sort(key=lambda x: x[2], reverse=True)
        
        # Try to execute on highest priority system first
        for system_name, adapter, priority in capable_systems:
            try:
                success = await adapter.write_control_command(command)
                if success:
                    logger.info(f"Command executed successfully on {system_name}")
                    return True
                else:
                    logger.warning(f"Command failed on {system_name}, trying next system")
            except Exception as e:
                logger.error(f"Command execution error on {system_name}: {e}")
        
        logger.error("Command execution failed on all capable systems")
        return False
    
    def _deduplicate_sensor_readings(self, readings: List[SensorReading]) -> List[SensorReading]:
        """Remove duplicate sensor readings, keeping highest priority."""
        sensor_map = {}
        
        for reading in readings:
            sensor_id = reading.sensor_id
            priority = reading.metadata.get("system_priority", 0)
            
            if sensor_id not in sensor_map or priority > sensor_map[sensor_id].metadata.get("system_priority", 0):
                sensor_map[sensor_id] = reading
        
        return list(sensor_map.values())
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integrated systems."""
        status = {
            "total_systems": len(self.adapters),
            "systems": {}
        }
        
        for system_name, adapter in self.adapters.items():
            try:
                system_status = await adapter.get_system_status()
                status["systems"][system_name] = {
                    "status": system_status,
                    "priority": self.system_priorities[system_name]
                }
            except Exception as e:
                status["systems"][system_name] = {
                    "status": {"connected": False, "error": str(e)},
                    "priority": self.system_priorities[system_name]
                }
        
        return status
