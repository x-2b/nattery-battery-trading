"""
Configuration management for Edge Bridge Service using Pydantic Settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Service Configuration
    PORT: int = Field(default=8000, description="Service port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    PYTHON_ENV: str = Field(default="production", description="Environment")
    
    # Modbus Configuration
    MODBUS_PORT: str = Field(default="/dev/ttyUSB0", description="Modbus serial port")
    MODBUS_BAUDRATE: int = Field(default=9600, description="Modbus baud rate")
    MODBUS_SLAVE_ID: int = Field(default=1, description="Modbus slave ID")
    MODBUS_TIMEOUT: int = Field(default=3, description="Modbus timeout in seconds")
    MODBUS_RETRY_COUNT: int = Field(default=3, description="Modbus retry attempts")
    MODBUS_RETRY_DELAY: float = Field(default=1.0, description="Delay between retries")
    
    # MQTT Configuration
    MQTT_BROKER_URL: str = Field(default="mqtt://mosquitto:1883", description="MQTT broker URL")
    MQTT_USERNAME: Optional[str] = Field(default="nattery", description="MQTT username")
    MQTT_PASSWORD: Optional[str] = Field(default="password", description="MQTT password")
    MQTT_CLIENT_ID: str = Field(default="edge-bridge", description="MQTT client ID")
    MQTT_KEEPALIVE: int = Field(default=60, description="MQTT keepalive interval")
    MQTT_QOS: int = Field(default=1, description="MQTT QoS level")
    
    # MQTT Topics
    MQTT_TOPIC_PREFIX: str = Field(default="nattery", description="MQTT topic prefix")
    MQTT_TOPIC_DATA: str = Field(default="data", description="Data topic")
    MQTT_TOPIC_COMMANDS: str = Field(default="commands", description="Commands topic")
    MQTT_TOPIC_STATUS: str = Field(default="status", description="Status topic")
    MQTT_TOPIC_ALERTS: str = Field(default="alerts", description="Alerts topic")
    
    # Data Collection
    DATA_COLLECTION_INTERVAL: int = Field(default=5, description="Data collection interval in seconds")
    BATCH_SIZE: int = Field(default=10, description="Number of registers to read in batch")
    
    # Health Monitoring
    HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Health check interval in seconds")
    MAX_CONSECUTIVE_FAILURES: int = Field(default=5, description="Max failures before marking unhealthy")
    
    # Command Queue
    MAX_QUEUE_SIZE: int = Field(default=100, description="Maximum command queue size")
    COMMAND_TIMEOUT: int = Field(default=30, description="Command execution timeout")
    
    # Redis Configuration (for command persistence)
    REDIS_URL: str = Field(default="redis://redis:6379", description="Redis connection URL")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_KEY_PREFIX: str = Field(default="edge-bridge", description="Redis key prefix")
    
    # Device Configuration
    DEVICE_ID: str = Field(default="inverter-001", description="Device identifier")
    DEVICE_TYPE: str = Field(default="inverter", description="Device type")
    DEVICE_MODEL: str = Field(default="growatt-spf-5000", description="Device model")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @property
    def mqtt_broker_host(self) -> str:
        """Extract host from MQTT broker URL."""
        if "://" in self.MQTT_BROKER_URL:
            return self.MQTT_BROKER_URL.split("://")[1].split(":")[0]
        return self.MQTT_BROKER_URL.split(":")[0]
    
    @property
    def mqtt_broker_port(self) -> int:
        """Extract port from MQTT broker URL."""
        if "://" in self.MQTT_BROKER_URL:
            url_part = self.MQTT_BROKER_URL.split("://")[1]
            if ":" in url_part:
                return int(url_part.split(":")[1])
        elif ":" in self.MQTT_BROKER_URL:
            return int(self.MQTT_BROKER_URL.split(":")[1])
        return 1883  # Default MQTT port
    
    def get_mqtt_topic(self, topic_type: str, device_id: Optional[str] = None) -> str:
        """Generate MQTT topic with proper structure."""
        device = device_id or self.DEVICE_ID
        return f"{self.MQTT_TOPIC_PREFIX}/{device}/{topic_type}"
    
    def get_redis_key(self, key_suffix: str) -> str:
        """Generate Redis key with prefix."""
        return f"{self.REDIS_KEY_PREFIX}:{key_suffix}" 