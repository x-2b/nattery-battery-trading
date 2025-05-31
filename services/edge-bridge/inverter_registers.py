"""
Inverter register definitions for Growatt SPF 5000 ES.

Based on the inverter datasheet, this module defines all Modbus registers
for reading battery status, inverter parameters, and control commands.
"""

from typing import Dict, Optional
from modbus_client import RegisterDefinition, ModbusDataType


class InverterRegisters:
    """Registry of all inverter Modbus registers."""
    
    def __init__(self):
        self.registers: Dict[str, RegisterDefinition] = {}
        self._initialize_registers()
    
    def _initialize_registers(self):
        """Initialize all register definitions."""
        
        # Battery Status Registers (Input Registers - Read Only)
        self._add_register("battery_voltage", 3027, ModbusDataType.UINT16, 0.1, "V", "Battery voltage")
        self._add_register("battery_current", 3028, ModbusDataType.INT16, 0.1, "A", "Battery current (+ charging, - discharging)")
        self._add_register("battery_power", 3029, ModbusDataType.INT16, 1.0, "W", "Battery power (+ charging, - discharging)")
        self._add_register("battery_soc", 3030, ModbusDataType.UINT16, 1.0, "%", "Battery state of charge")
        self._add_register("battery_temperature", 3031, ModbusDataType.INT16, 0.1, "°C", "Battery temperature")
        
        # AC Output Registers
        self._add_register("ac_voltage_output", 3033, ModbusDataType.UINT16, 0.1, "V", "AC output voltage")
        self._add_register("ac_current_output", 3034, ModbusDataType.UINT16, 0.1, "A", "AC output current")
        self._add_register("ac_power_output", 3035, ModbusDataType.UINT16, 1.0, "W", "AC output power")
        self._add_register("ac_frequency_output", 3036, ModbusDataType.UINT16, 0.01, "Hz", "AC output frequency")
        
        # AC Input/Grid Registers
        self._add_register("ac_voltage_input", 3037, ModbusDataType.UINT16, 0.1, "V", "AC input voltage")
        self._add_register("ac_current_input", 3038, ModbusDataType.UINT16, 0.1, "A", "AC input current")
        self._add_register("ac_power_input", 3039, ModbusDataType.UINT16, 1.0, "W", "AC input power")
        self._add_register("ac_frequency_input", 3040, ModbusDataType.UINT16, 0.01, "Hz", "AC input frequency")
        
        # PV Solar Registers
        self._add_register("pv_voltage", 3021, ModbusDataType.UINT16, 0.1, "V", "PV input voltage")
        self._add_register("pv_current", 3022, ModbusDataType.UINT16, 0.1, "A", "PV input current")
        self._add_register("pv_power", 3023, ModbusDataType.UINT16, 1.0, "W", "PV input power")
        
        # Load Registers
        self._add_register("load_voltage", 3041, ModbusDataType.UINT16, 0.1, "V", "Load voltage")
        self._add_register("load_current", 3042, ModbusDataType.UINT16, 0.1, "A", "Load current")
        self._add_register("load_power", 3043, ModbusDataType.UINT16, 1.0, "W", "Load power")
        self._add_register("load_percentage", 3044, ModbusDataType.UINT16, 1.0, "%", "Load percentage")
        
        # System Status Registers
        self._add_register("working_mode", 3045, ModbusDataType.UINT16, 1.0, "", "Working mode")
        self._add_register("inverter_temperature", 3046, ModbusDataType.INT16, 0.1, "°C", "Inverter temperature")
        self._add_register("fault_code", 3047, ModbusDataType.UINT16, 1.0, "", "Fault code")
        self._add_register("warning_code", 3048, ModbusDataType.UINT16, 1.0, "", "Warning code")
        
        # Energy Statistics (32-bit registers)
        self._add_register("pv_energy_today", 3049, ModbusDataType.UINT32, 0.1, "kWh", "PV energy today")
        self._add_register("pv_energy_total", 3051, ModbusDataType.UINT32, 0.1, "kWh", "PV energy total")
        self._add_register("load_energy_today", 3053, ModbusDataType.UINT32, 0.1, "kWh", "Load energy today")
        self._add_register("load_energy_total", 3055, ModbusDataType.UINT32, 0.1, "kWh", "Load energy total")
        self._add_register("battery_charge_today", 3057, ModbusDataType.UINT32, 0.1, "kWh", "Battery charge today")
        self._add_register("battery_discharge_today", 3059, ModbusDataType.UINT32, 0.1, "kWh", "Battery discharge today")
        
        # Control Registers (Holding Registers - Read/Write)
        self._add_register("output_source_priority", 1, ModbusDataType.UINT16, 1.0, "", "Output source priority", True)
        self._add_register("charger_source_priority", 2, ModbusDataType.UINT16, 1.0, "", "Charger source priority", True)
        self._add_register("battery_type", 3, ModbusDataType.UINT16, 1.0, "", "Battery type", True)
        self._add_register("battery_capacity", 4, ModbusDataType.UINT16, 1.0, "Ah", "Battery capacity", True)
        
        # Battery Charge/Discharge Control
        self._add_register("max_charge_current", 5, ModbusDataType.UINT16, 1.0, "A", "Maximum charge current", True)
        self._add_register("max_discharge_current", 6, ModbusDataType.UINT16, 1.0, "A", "Maximum discharge current", True)
        self._add_register("battery_low_voltage", 7, ModbusDataType.UINT16, 0.1, "V", "Battery low voltage cutoff", True)
        self._add_register("battery_high_voltage", 8, ModbusDataType.UINT16, 0.1, "V", "Battery high voltage cutoff", True)
        
        # Time-based Control
        self._add_register("charge_time_1_start", 9, ModbusDataType.UINT16, 1.0, "", "Charge time 1 start (HHMM)", True)
        self._add_register("charge_time_1_end", 10, ModbusDataType.UINT16, 1.0, "", "Charge time 1 end (HHMM)", True)
        self._add_register("charge_time_2_start", 11, ModbusDataType.UINT16, 1.0, "", "Charge time 2 start (HHMM)", True)
        self._add_register("charge_time_2_end", 12, ModbusDataType.UINT16, 1.0, "", "Charge time 2 end (HHMM)", True)
        
        # Discharge Control
        self._add_register("discharge_time_1_start", 13, ModbusDataType.UINT16, 1.0, "", "Discharge time 1 start (HHMM)", True)
        self._add_register("discharge_time_1_end", 14, ModbusDataType.UINT16, 1.0, "", "Discharge time 1 end (HHMM)", True)
        self._add_register("discharge_time_2_start", 15, ModbusDataType.UINT16, 1.0, "", "Discharge time 2 start (HHMM)", True)
        self._add_register("discharge_time_2_end", 16, ModbusDataType.UINT16, 1.0, "", "Discharge time 2 end (HHMM)", True)
        
        # Advanced Control
        self._add_register("enable_charge", 17, ModbusDataType.UINT16, 1.0, "", "Enable battery charge (0=disable, 1=enable)", True)
        self._add_register("enable_discharge", 18, ModbusDataType.UINT16, 1.0, "", "Enable battery discharge (0=disable, 1=enable)", True)
        self._add_register("force_charge", 19, ModbusDataType.UINT16, 1.0, "", "Force charge from grid (0=disable, 1=enable)", True)
        
        # Power Control
        self._add_register("charge_power_limit", 20, ModbusDataType.UINT16, 1.0, "W", "Charge power limit", True)
        self._add_register("discharge_power_limit", 21, ModbusDataType.UINT16, 1.0, "W", "Discharge power limit", True)
        
        # Grid Control
        self._add_register("grid_charge_enabled", 22, ModbusDataType.UINT16, 1.0, "", "Grid charge enabled", True)
        self._add_register("grid_discharge_enabled", 23, ModbusDataType.UINT16, 1.0, "", "Grid discharge enabled", True)
    
    def _add_register(
        self, 
        name: str, 
        address: int, 
        data_type: ModbusDataType, 
        scale: float = 1.0,
        unit: str = "",
        description: str = "",
        writable: bool = False
    ):
        """Add a register definition."""
        self.registers[name] = RegisterDefinition(
            address=address,
            name=name,
            data_type=data_type,
            scale=scale,
            unit=unit,
            description=description,
            writable=writable
        )
    
    def get_register(self, name: str) -> Optional[RegisterDefinition]:
        """Get register definition by name."""
        return self.registers.get(name)
    
    def get_all_registers(self) -> Dict[str, RegisterDefinition]:
        """Get all register definitions."""
        return self.registers.copy()
    
    def get_readable_registers(self) -> Dict[str, RegisterDefinition]:
        """Get all readable registers."""
        return {name: reg for name, reg in self.registers.items()}
    
    def get_writable_registers(self) -> Dict[str, RegisterDefinition]:
        """Get all writable registers."""
        return {name: reg for name, reg in self.registers.items() if reg.writable}
    
    def get_registers_by_type(self, register_type: str) -> Dict[str, RegisterDefinition]:
        """Get registers by type (holding or input)."""
        if register_type == "holding":
            return {name: reg for name, reg in self.registers.items() if reg.address < 30000}
        elif register_type == "input":
            return {name: reg for name, reg in self.registers.items() if reg.address >= 30000}
        else:
            return {}
    
    def get_working_mode_description(self, mode_value: int) -> str:
        """Get human-readable working mode description."""
        modes = {
            0: "Power On",
            1: "Standby",
            2: "Line Mode",
            3: "Battery Mode", 
            4: "Fault Mode",
            5: "Hybrid Mode",
            6: "Charge Mode",
            7: "Bypass Mode"
        }
        return modes.get(mode_value, f"Unknown Mode ({mode_value})")
    
    def get_fault_description(self, fault_code: int) -> str:
        """Get human-readable fault description."""
        faults = {
            0: "No Fault",
            1: "Fan Error",
            2: "Over Temperature",
            3: "Battery Voltage High",
            4: "Battery Voltage Low", 
            5: "Output Short Circuit",
            6: "Output Voltage High",
            7: "Over Load Timeout",
            8: "Bus Voltage High",
            9: "Bus Soft Start Failed",
            10: "Main Relay Failed",
            11: "Output Voltage Low",
            12: "Inverter Soft Start Failed",
            13: "Self Test Failed",
            14: "OP DC Voltage Over",
            15: "Bat Open",
            16: "Current Sensor Failed",
            17: "Battery Short",
            18: "Power Limit",
            19: "PV Voltage High",
            20: "MPPT Overload Fault",
            21: "MPPT Overload Warning",
            22: "Battery Too Low to Charge"
        }
        return faults.get(fault_code, f"Unknown Fault ({fault_code})")
    
    def get_battery_type_description(self, battery_type: int) -> str:
        """Get human-readable battery type description."""
        types = {
            0: "AGM",
            1: "Flooded",
            2: "User Defined",
            3: "Lithium"
        }
        return types.get(battery_type, f"Unknown Type ({battery_type})")
    
    def get_priority_description(self, priority: int) -> str:
        """Get human-readable priority description."""
        priorities = {
            0: "Utility First",
            1: "Solar First", 
            2: "SBU (Solar-Battery-Utility)"
        }
        return priorities.get(priority, f"Unknown Priority ({priority})") 