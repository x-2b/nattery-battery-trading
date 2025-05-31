"""
Data publisher for collecting inverter data and publishing to MQTT.

Handles periodic data collection from Modbus and publishing to MQTT topics
for consumption by microservices.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from config import Settings
from mqtt_client import MQTTClient

logger = logging.getLogger(__name__)


class DataPublisher:
    """Handles data collection and MQTT publishing."""
    
    def __init__(self, mqtt_client: MQTTClient, settings: Settings):
        self.mqtt_client = mqtt_client
        self.settings = settings
        self.last_data: Optional[Dict[str, Any]] = None
        self.collection_count = 0
        self.error_count = 0
        
        logger.info("Data publisher initialized")
    
    async def collect_and_publish(self, modbus_client=None):
        """Collect data from Modbus and publish to MQTT."""
        try:
            if not modbus_client or not modbus_client.is_connected():
                logger.warning("Modbus client not available for data collection")
                return
            
            # Collect all data registers
            data = await modbus_client.read_all_data_registers()
            
            if data:
                # Add derived calculations
                enhanced_data = self._enhance_data(data)
                
                # Publish to MQTT
                success = await self.mqtt_client.publish_device_data(enhanced_data)
                
                if success:
                    self.last_data = enhanced_data
                    self.collection_count += 1
                    logger.debug(f"Published data collection #{self.collection_count}")
                else:
                    self.error_count += 1
                    logger.error("Failed to publish data to MQTT")
            else:
                self.error_count += 1
                logger.warning("No data collected from Modbus")
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error in data collection: {e}")
    
    def _enhance_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance raw data with calculated values and metadata."""
        enhanced = raw_data.copy()
        
        try:
            # Calculate power efficiency
            pv_power = raw_data.get("pv_power", 0)
            battery_power = raw_data.get("battery_power", 0)
            load_power = raw_data.get("load_power", 0)
            
            # Energy flow calculations
            if pv_power > 0:
                if battery_power > 0:  # Charging
                    enhanced["energy_flow"] = "pv_to_battery_and_load"
                else:  # Discharging or direct use
                    enhanced["energy_flow"] = "pv_to_load"
            elif battery_power < 0:  # Discharging
                enhanced["energy_flow"] = "battery_to_load"
            else:
                enhanced["energy_flow"] = "grid_to_load"
            
            # Power balance
            enhanced["power_balance"] = pv_power + battery_power - load_power
            
            # Battery status
            soc = raw_data.get("battery_soc", 0)
            if soc > 90:
                enhanced["battery_status"] = "full"
            elif soc > 50:
                enhanced["battery_status"] = "good"
            elif soc > 20:
                enhanced["battery_status"] = "low"
            else:
                enhanced["battery_status"] = "critical"
            
            # System efficiency (if both input and output power available)
            ac_power_output = raw_data.get("ac_power_output", 0)
            ac_power_input = raw_data.get("ac_power_input", 0)
            
            if ac_power_input > 0:
                enhanced["system_efficiency"] = round((ac_power_output / ac_power_input) * 100, 2)
            
            # Working mode description
            working_mode = raw_data.get("working_mode")
            if working_mode is not None:
                from inverter_registers import InverterRegisters
                registers = InverterRegisters()
                enhanced["working_mode_description"] = registers.get_working_mode_description(working_mode)
            
            # Fault description
            fault_code = raw_data.get("fault_code")
            if fault_code is not None:
                from inverter_registers import InverterRegisters
                registers = InverterRegisters()
                enhanced["fault_description"] = registers.get_fault_description(fault_code)
            
            # Add collection metadata
            enhanced["collection_metadata"] = {
                "collection_time": datetime.utcnow().isoformat(),
                "collection_count": self.collection_count,
                "data_quality": self._assess_data_quality(raw_data)
            }
            
        except Exception as e:
            logger.error(f"Error enhancing data: {e}")
        
        return enhanced
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> str:
        """Assess the quality of collected data."""
        if not data:
            return "no_data"
        
        # Check for critical missing values
        critical_fields = ["battery_voltage", "battery_soc", "working_mode"]
        missing_critical = [field for field in critical_fields if field not in data or data[field] is None]
        
        if missing_critical:
            return "poor"
        
        # Check for reasonable value ranges
        battery_voltage = data.get("battery_voltage", 0)
        battery_soc = data.get("battery_soc", 0)
        
        if battery_voltage < 10 or battery_voltage > 60:  # Unreasonable voltage
            return "questionable"
        
        if battery_soc < 0 or battery_soc > 100:  # Invalid SOC
            return "questionable"
        
        # Check data completeness
        total_fields = len(data)
        if total_fields < 5:
            return "limited"
        elif total_fields < 10:
            return "good"
        else:
            return "excellent"
    
    async def publish_status_update(self, status_data: Dict[str, Any]):
        """Publish a status update."""
        try:
            await self.mqtt_client.publish_device_status(status_data)
        except Exception as e:
            logger.error(f"Error publishing status update: {e}")
    
    async def publish_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """Publish an alert."""
        try:
            await self.mqtt_client.publish_alert(alert_type, message, severity)
        except Exception as e:
            logger.error(f"Error publishing alert: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get data collection statistics."""
        success_rate = 0
        if self.collection_count + self.error_count > 0:
            success_rate = (self.collection_count / (self.collection_count + self.error_count)) * 100
        
        return {
            "collection_count": self.collection_count,
            "error_count": self.error_count,
            "success_rate": round(success_rate, 2),
            "last_collection": self.last_data.get("collection_metadata", {}).get("collection_time") if self.last_data else None,
            "last_data_quality": self.last_data.get("collection_metadata", {}).get("data_quality") if self.last_data else None
        } 