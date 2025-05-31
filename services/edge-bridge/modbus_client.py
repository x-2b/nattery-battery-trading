"""
Modbus RTU client for communicating with the inverter.

Critical constraints:
- All Modbus operations must be serialized (no concurrent access)
- Inverter firmware cannot handle concurrent commands
- Proper error handling and retry logic required
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException, ConnectionException
from pymodbus.pdu import ExceptionResponse

from config import Settings
from inverter_registers import InverterRegisters

logger = logging.getLogger(__name__)


class ModbusDataType(Enum):
    """Modbus data types for register interpretation."""
    UINT16 = "uint16"
    INT16 = "int16"
    UINT32 = "uint32"
    INT32 = "int32"
    FLOAT32 = "float32"
    BOOL = "bool"


@dataclass
class RegisterDefinition:
    """Definition of a Modbus register."""
    address: int
    name: str
    data_type: ModbusDataType
    scale: float = 1.0
    unit: str = ""
    description: str = ""
    writable: bool = False


class ModbusClient:
    """Async Modbus RTU client with serialized access and error handling."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Optional[AsyncModbusSerialClient] = None
        self.connected = False
        self.lock = asyncio.Lock()  # Ensure serialized access
        self.consecutive_failures = 0
        self.registers = InverterRegisters()
        
        logger.info(f"Initializing Modbus client for {settings.MODBUS_PORT}")
    
    async def connect(self) -> bool:
        """Connect to the Modbus device."""
        try:
            self.client = AsyncModbusSerialClient(
                port=self.settings.MODBUS_PORT,
                baudrate=self.settings.MODBUS_BAUDRATE,
                timeout=self.settings.MODBUS_TIMEOUT,
                parity='N',
                stopbits=1,
                bytesize=8
            )
            
            connection_result = await self.client.connect()
            if connection_result:
                self.connected = True
                self.consecutive_failures = 0
                logger.info(f"Connected to Modbus device on {self.settings.MODBUS_PORT}")
                return True
            else:
                logger.error("Failed to connect to Modbus device")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Modbus device: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the Modbus device."""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("Disconnected from Modbus device")
    
    def is_connected(self) -> bool:
        """Check if connected to Modbus device."""
        return self.connected and self.client is not None
    
    async def read_holding_registers(
        self, 
        address: int, 
        count: int = 1,
        slave_id: Optional[int] = None
    ) -> Optional[List[int]]:
        """Read holding registers with retry logic."""
        if not self.is_connected():
            logger.error("Modbus client not connected")
            return None
        
        slave = slave_id or self.settings.MODBUS_SLAVE_ID
        
        async with self.lock:  # Serialize all Modbus operations
            for attempt in range(self.settings.MODBUS_RETRY_COUNT):
                try:
                    result = await self.client.read_holding_registers(
                        address=address,
                        count=count,
                        slave=slave
                    )
                    
                    if result.isError():
                        logger.warning(f"Modbus error reading registers {address}-{address+count-1}: {result}")
                        if attempt < self.settings.MODBUS_RETRY_COUNT - 1:
                            await asyncio.sleep(self.settings.MODBUS_RETRY_DELAY)
                            continue
                        else:
                            self.consecutive_failures += 1
                            return None
                    
                    self.consecutive_failures = 0
                    return result.registers
                    
                except Exception as e:
                    logger.error(f"Exception reading registers {address}-{address+count-1}: {e}")
                    if attempt < self.settings.MODBUS_RETRY_COUNT - 1:
                        await asyncio.sleep(self.settings.MODBUS_RETRY_DELAY)
                        continue
                    else:
                        self.consecutive_failures += 1
                        return None
        
        return None
    
    async def write_holding_register(
        self, 
        address: int, 
        value: int,
        slave_id: Optional[int] = None
    ) -> bool:
        """Write a single holding register with retry logic."""
        if not self.is_connected():
            logger.error("Modbus client not connected")
            return False
        
        slave = slave_id or self.settings.MODBUS_SLAVE_ID
        
        async with self.lock:  # Serialize all Modbus operations
            for attempt in range(self.settings.MODBUS_RETRY_COUNT):
                try:
                    result = await self.client.write_register(
                        address=address,
                        value=value,
                        slave=slave
                    )
                    
                    if result.isError():
                        logger.warning(f"Modbus error writing register {address}: {result}")
                        if attempt < self.settings.MODBUS_RETRY_COUNT - 1:
                            await asyncio.sleep(self.settings.MODBUS_RETRY_DELAY)
                            continue
                        else:
                            self.consecutive_failures += 1
                            return False
                    
                    self.consecutive_failures = 0
                    logger.info(f"Successfully wrote value {value} to register {address}")
                    return True
                    
                except Exception as e:
                    logger.error(f"Exception writing register {address}: {e}")
                    if attempt < self.settings.MODBUS_RETRY_COUNT - 1:
                        await asyncio.sleep(self.settings.MODBUS_RETRY_DELAY)
                        continue
                    else:
                        self.consecutive_failures += 1
                        return False
        
        return False
    
    async def read_input_registers(
        self, 
        address: int, 
        count: int = 1,
        slave_id: Optional[int] = None
    ) -> Optional[List[int]]:
        """Read input registers with retry logic."""
        if not self.is_connected():
            logger.error("Modbus client not connected")
            return None
        
        slave = slave_id or self.settings.MODBUS_SLAVE_ID
        
        async with self.lock:  # Serialize all Modbus operations
            for attempt in range(self.settings.MODBUS_RETRY_COUNT):
                try:
                    result = await self.client.read_input_registers(
                        address=address,
                        count=count,
                        slave=slave
                    )
                    
                    if result.isError():
                        logger.warning(f"Modbus error reading input registers {address}-{address+count-1}: {result}")
                        if attempt < self.settings.MODBUS_RETRY_COUNT - 1:
                            await asyncio.sleep(self.settings.MODBUS_RETRY_DELAY)
                            continue
                        else:
                            self.consecutive_failures += 1
                            return None
                    
                    self.consecutive_failures = 0
                    return result.registers
                    
                except Exception as e:
                    logger.error(f"Exception reading input registers {address}-{address+count-1}: {e}")
                    if attempt < self.settings.MODBUS_RETRY_COUNT - 1:
                        await asyncio.sleep(self.settings.MODBUS_RETRY_DELAY)
                        continue
                    else:
                        self.consecutive_failures += 1
                        return None
        
        return None
    
    def convert_register_value(
        self, 
        raw_values: List[int], 
        data_type: ModbusDataType,
        scale: float = 1.0
    ) -> Union[int, float, bool]:
        """Convert raw register values to proper data type."""
        if not raw_values:
            return None
        
        try:
            if data_type == ModbusDataType.UINT16:
                return int(raw_values[0] * scale)
            
            elif data_type == ModbusDataType.INT16:
                # Convert unsigned to signed 16-bit
                value = raw_values[0]
                if value > 32767:
                    value -= 65536
                return int(value * scale)
            
            elif data_type == ModbusDataType.UINT32:
                # Combine two 16-bit registers (high, low)
                if len(raw_values) < 2:
                    return None
                value = (raw_values[0] << 16) | raw_values[1]
                return int(value * scale)
            
            elif data_type == ModbusDataType.INT32:
                # Combine two 16-bit registers and convert to signed
                if len(raw_values) < 2:
                    return None
                value = (raw_values[0] << 16) | raw_values[1]
                if value > 2147483647:
                    value -= 4294967296
                return int(value * scale)
            
            elif data_type == ModbusDataType.FLOAT32:
                # IEEE 754 float from two registers
                if len(raw_values) < 2:
                    return None
                import struct
                packed = struct.pack('>HH', raw_values[0], raw_values[1])
                value = struct.unpack('>f', packed)[0]
                return float(value * scale)
            
            elif data_type == ModbusDataType.BOOL:
                return bool(raw_values[0])
            
            else:
                logger.warning(f"Unknown data type: {data_type}")
                return raw_values[0]
                
        except Exception as e:
            logger.error(f"Error converting register value: {e}")
            return None
    
    async def read_register_by_name(self, register_name: str) -> Optional[Any]:
        """Read a register by its name using the register definition."""
        register_def = self.registers.get_register(register_name)
        if not register_def:
            logger.error(f"Unknown register: {register_name}")
            return None
        
        # Determine how many registers to read based on data type
        count = 2 if register_def.data_type in [ModbusDataType.UINT32, ModbusDataType.INT32, ModbusDataType.FLOAT32] else 1
        
        # Read the appropriate register type
        if register_def.address < 30000:
            raw_values = await self.read_holding_registers(register_def.address, count)
        else:
            raw_values = await self.read_input_registers(register_def.address - 30000, count)
        
        if raw_values is None:
            return None
        
        return self.convert_register_value(raw_values, register_def.data_type, register_def.scale)
    
    async def write_register_by_name(self, register_name: str, value: Union[int, float]) -> bool:
        """Write a register by its name using the register definition."""
        register_def = self.registers.get_register(register_name)
        if not register_def:
            logger.error(f"Unknown register: {register_name}")
            return False
        
        if not register_def.writable:
            logger.error(f"Register {register_name} is not writable")
            return False
        
        # Convert value based on data type and scale
        try:
            if register_def.data_type in [ModbusDataType.UINT16, ModbusDataType.INT16]:
                scaled_value = int(value / register_def.scale)
                return await self.write_holding_register(register_def.address, scaled_value)
            else:
                logger.error(f"Writing {register_def.data_type} registers not yet implemented")
                return False
                
        except Exception as e:
            logger.error(f"Error writing register {register_name}: {e}")
            return False
    
    async def read_all_data_registers(self) -> Dict[str, Any]:
        """Read all important data registers for monitoring."""
        data = {}
        
        # Read key registers for battery and inverter status
        key_registers = [
            "battery_voltage",
            "battery_current", 
            "battery_power",
            "battery_soc",
            "battery_temperature",
            "ac_voltage_output",
            "ac_current_output",
            "ac_power_output",
            "pv_voltage",
            "pv_current",
            "pv_power",
            "inverter_temperature",
            "working_mode",
            "fault_code"
        ]
        
        for register_name in key_registers:
            try:
                value = await self.read_register_by_name(register_name)
                if value is not None:
                    data[register_name] = value
                await asyncio.sleep(0.1)  # Small delay between reads
            except Exception as e:
                logger.error(f"Error reading {register_name}: {e}")
        
        return data
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the Modbus connection."""
        return {
            "connected": self.connected,
            "consecutive_failures": self.consecutive_failures,
            "max_failures": self.settings.MAX_CONSECUTIVE_FAILURES,
            "healthy": self.connected and self.consecutive_failures < self.settings.MAX_CONSECUTIVE_FAILURES
        } 