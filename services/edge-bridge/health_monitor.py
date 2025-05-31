"""
Health monitor for Edge Bridge Service.

Monitors the health of Modbus connection, MQTT connection, and overall system
performance with alerting capabilities.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from config import Settings
from modbus_client import ModbusClient
from mqtt_client import MQTTClient

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitors system health and publishes alerts."""
    
    def __init__(self, modbus_client: ModbusClient, mqtt_client: MQTTClient):
        self.modbus_client = modbus_client
        self.mqtt_client = mqtt_client
        self.settings = Settings()
        
        # Health tracking
        self.last_health_check = None
        self.consecutive_failures = 0
        self.health_history = []
        self.alerts_sent = set()
        
        # Performance metrics
        self.start_time = datetime.utcnow()
        self.total_checks = 0
        self.failed_checks = 0
        
        logger.info("Health monitor initialized")
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        self.total_checks += 1
        self.last_health_check = datetime.utcnow()
        
        health_status = {
            "timestamp": self.last_health_check.isoformat(),
            "overall_status": "healthy",
            "components": {},
            "alerts": []
        }
        
        try:
            # Check Modbus connection
            modbus_health = await self._check_modbus_health()
            health_status["components"]["modbus"] = modbus_health
            
            # Check MQTT connection
            mqtt_health = self._check_mqtt_health()
            health_status["components"]["mqtt"] = mqtt_health
            
            # Check system resources
            system_health = self._check_system_health()
            health_status["components"]["system"] = system_health
            
            # Determine overall health
            component_statuses = [comp["status"] for comp in health_status["components"].values()]
            
            if "critical" in component_statuses:
                health_status["overall_status"] = "critical"
                self.consecutive_failures += 1
            elif "unhealthy" in component_statuses:
                health_status["overall_status"] = "unhealthy"
                self.consecutive_failures += 1
            else:
                health_status["overall_status"] = "healthy"
                self.consecutive_failures = 0
            
            # Generate alerts if needed
            await self._process_health_alerts(health_status)
            
            # Store in history (keep last 100 checks)
            self.health_history.append(health_status)
            if len(self.health_history) > 100:
                self.health_history.pop(0)
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            health_status["overall_status"] = "error"
            health_status["error"] = str(e)
            self.failed_checks += 1
        
        return health_status
    
    async def _check_modbus_health(self) -> Dict[str, Any]:
        """Check Modbus connection health."""
        health = {
            "status": "healthy",
            "connected": False,
            "consecutive_failures": 0,
            "last_successful_read": None,
            "response_time": None
        }
        
        try:
            if not self.modbus_client.is_connected():
                health["status"] = "critical"
                health["connected"] = False
                return health
            
            health["connected"] = True
            health["consecutive_failures"] = self.modbus_client.consecutive_failures
            
            # Test read operation with timing
            start_time = datetime.utcnow()
            test_result = await self.modbus_client.read_register_by_name("battery_voltage")
            end_time = datetime.utcnow()
            
            if test_result is not None:
                health["last_successful_read"] = end_time.isoformat()
                health["response_time"] = (end_time - start_time).total_seconds()
                
                # Check response time
                if health["response_time"] > 5.0:  # Slow response
                    health["status"] = "unhealthy"
                    health["issue"] = "slow_response"
            else:
                health["status"] = "unhealthy"
                health["issue"] = "read_failed"
            
            # Check consecutive failures
            if health["consecutive_failures"] >= self.settings.MAX_CONSECUTIVE_FAILURES:
                health["status"] = "critical"
                health["issue"] = "too_many_failures"
            
        except Exception as e:
            health["status"] = "critical"
            health["error"] = str(e)
        
        return health
    
    def _check_mqtt_health(self) -> Dict[str, Any]:
        """Check MQTT connection health."""
        health = {
            "status": "healthy",
            "connected": False,
            "broker_host": self.settings.mqtt_broker_host,
            "broker_port": self.settings.mqtt_broker_port
        }
        
        try:
            health["connected"] = self.mqtt_client.is_connected()
            
            if not health["connected"]:
                health["status"] = "critical"
                health["issue"] = "disconnected"
            
        except Exception as e:
            health["status"] = "critical"
            health["error"] = str(e)
        
        return health
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check system resource health."""
        health = {
            "status": "healthy",
            "uptime": None,
            "memory_usage": None,
            "disk_usage": None
        }
        
        try:
            # Calculate uptime
            uptime = datetime.utcnow() - self.start_time
            health["uptime"] = str(uptime)
            
            # Check memory usage (basic check)
            import psutil
            memory = psutil.virtual_memory()
            health["memory_usage"] = {
                "percent": memory.percent,
                "available_mb": memory.available // (1024 * 1024)
            }
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            health["disk_usage"] = {
                "percent": (disk.used / disk.total) * 100,
                "free_gb": disk.free // (1024 * 1024 * 1024)
            }
            
            # Assess health based on resource usage
            if memory.percent > 90:
                health["status"] = "critical"
                health["issue"] = "high_memory_usage"
            elif memory.percent > 80:
                health["status"] = "unhealthy"
                health["issue"] = "elevated_memory_usage"
            
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 95:
                health["status"] = "critical"
                health["issue"] = "disk_full"
            elif disk_percent > 85:
                health["status"] = "unhealthy"
                health["issue"] = "disk_space_low"
            
        except ImportError:
            # psutil not available, basic health check
            health["status"] = "unknown"
            health["issue"] = "monitoring_unavailable"
        except Exception as e:
            health["status"] = "error"
            health["error"] = str(e)
        
        return health
    
    async def _process_health_alerts(self, health_status: Dict[str, Any]):
        """Process health status and send alerts if needed."""
        overall_status = health_status["overall_status"]
        
        # Critical system alert
        if overall_status == "critical":
            alert_key = "system_critical"
            if alert_key not in self.alerts_sent:
                await self._send_alert(
                    "system_health",
                    "System health is critical - immediate attention required",
                    "critical"
                )
                self.alerts_sent.add(alert_key)
        
        # Modbus connection alerts
        modbus_status = health_status["components"].get("modbus", {})
        if not modbus_status.get("connected", False):
            alert_key = "modbus_disconnected"
            if alert_key not in self.alerts_sent:
                await self._send_alert(
                    "modbus_connection",
                    "Modbus connection lost - hardware communication unavailable",
                    "critical"
                )
                self.alerts_sent.add(alert_key)
        else:
            # Clear alert if connection restored
            self.alerts_sent.discard("modbus_disconnected")
        
        # MQTT connection alerts
        mqtt_status = health_status["components"].get("mqtt", {})
        if not mqtt_status.get("connected", False):
            alert_key = "mqtt_disconnected"
            if alert_key not in self.alerts_sent:
                await self._send_alert(
                    "mqtt_connection",
                    "MQTT connection lost - communication with services unavailable",
                    "critical"
                )
                self.alerts_sent.add(alert_key)
        else:
            # Clear alert if connection restored
            self.alerts_sent.discard("mqtt_disconnected")
        
        # Performance alerts
        if self.consecutive_failures >= 3:
            alert_key = "consecutive_failures"
            if alert_key not in self.alerts_sent:
                await self._send_alert(
                    "performance",
                    f"Multiple consecutive health check failures ({self.consecutive_failures})",
                    "warning"
                )
                self.alerts_sent.add(alert_key)
        else:
            self.alerts_sent.discard("consecutive_failures")
    
    async def _send_alert(self, alert_type: str, message: str, severity: str):
        """Send an alert via MQTT."""
        try:
            if self.mqtt_client.is_connected():
                await self.mqtt_client.publish_alert(alert_type, message, severity)
                logger.warning(f"Health alert sent: {alert_type} - {message}")
            else:
                logger.error(f"Cannot send alert - MQTT disconnected: {message}")
        except Exception as e:
            logger.error(f"Error sending health alert: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        if not self.last_health_check:
            return {
                "status": "unknown",
                "message": "No health checks performed yet"
            }
        
        # Return the most recent health check
        if self.health_history:
            latest = self.health_history[-1]
            return {
                "status": latest["overall_status"],
                "timestamp": latest["timestamp"],
                "components": latest["components"],
                "consecutive_failures": self.consecutive_failures
            }
        
        return {
            "status": "error",
            "message": "Health check data unavailable"
        }
    
    def get_health_statistics(self) -> Dict[str, Any]:
        """Get health monitoring statistics."""
        success_rate = 0
        if self.total_checks > 0:
            success_rate = ((self.total_checks - self.failed_checks) / self.total_checks) * 100
        
        uptime = datetime.utcnow() - self.start_time
        
        return {
            "uptime": str(uptime),
            "total_checks": self.total_checks,
            "failed_checks": self.failed_checks,
            "success_rate": round(success_rate, 2),
            "consecutive_failures": self.consecutive_failures,
            "active_alerts": len(self.alerts_sent),
            "last_check": self.last_health_check.isoformat() if self.last_health_check else None
        } 