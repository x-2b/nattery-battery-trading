"""
MQTT client for publishing inverter data and receiving commands.

Handles communication between the Edge Bridge and the microservices
via MQTT broker with proper error handling and reconnection logic.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage

from config import Settings

logger = logging.getLogger(__name__)


class MQTTClient:
    """Async MQTT client for Edge Bridge communication."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.message_handlers: Dict[str, Callable] = {}
        self.last_will_topic = self.settings.get_mqtt_topic("status")
        
        logger.info(f"Initializing MQTT client for {settings.MQTT_BROKER_URL}")
    
    async def connect(self) -> bool:
        """Connect to MQTT broker with authentication."""
        try:
            self.client = mqtt.Client(
                client_id=self.settings.MQTT_CLIENT_ID,
                protocol=mqtt.MQTTv311,
                transport="tcp"
            )
            
            # Set authentication if provided
            if self.settings.MQTT_USERNAME and self.settings.MQTT_PASSWORD:
                self.client.username_pw_set(
                    self.settings.MQTT_USERNAME,
                    self.settings.MQTT_PASSWORD
                )
            
            # Set last will and testament
            last_will_payload = json.dumps({
                "device_id": self.settings.DEVICE_ID,
                "status": "offline",
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "unexpected_disconnect"
            })
            
            self.client.will_set(
                self.last_will_topic,
                last_will_payload,
                qos=self.settings.MQTT_QOS,
                retain=True
            )
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_publish = self._on_publish
            self.client.on_subscribe = self._on_subscribe
            
            # Connect to broker
            result = self.client.connect(
                self.settings.mqtt_broker_host,
                self.settings.mqtt_broker_port,
                self.settings.MQTT_KEEPALIVE
            )
            
            if result == mqtt.MQTT_ERR_SUCCESS:
                # Start the network loop
                self.client.loop_start()
                
                # Wait for connection
                for _ in range(50):  # 5 second timeout
                    if self.connected:
                        break
                    await asyncio.sleep(0.1)
                
                if self.connected:
                    logger.info("Connected to MQTT broker")
                    await self._publish_online_status()
                    await self._subscribe_to_commands()
                    return True
                else:
                    logger.error("Failed to connect to MQTT broker within timeout")
                    return False
            else:
                logger.error(f"Failed to connect to MQTT broker: {mqtt.error_string(result)}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client and self.connected:
            # Publish offline status
            await self._publish_offline_status()
            
            # Disconnect
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from MQTT broker")
    
    def is_connected(self) -> bool:
        """Check if connected to MQTT broker."""
        return self.connected
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            self.connected = True
            logger.info("MQTT connection established")
        else:
            self.connected = False
            logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection: {rc}")
        else:
            logger.info("MQTT disconnection")
    
    def _on_message(self, client, userdata, msg: MQTTMessage):
        """Callback for received MQTT messages."""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.debug(f"Received MQTT message on {topic}: {payload}")
            
            # Route message to appropriate handler
            for pattern, handler in self.message_handlers.items():
                if pattern in topic:
                    asyncio.create_task(handler(topic, payload))
                    break
            else:
                logger.warning(f"No handler for MQTT topic: {topic}")
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for published messages."""
        logger.debug(f"MQTT message published: {mid}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for subscription confirmation."""
        logger.debug(f"MQTT subscription confirmed: {mid}, QoS: {granted_qos}")
    
    async def publish(
        self, 
        topic: str, 
        payload: Dict[str, Any], 
        qos: Optional[int] = None,
        retain: bool = False
    ) -> bool:
        """Publish a message to MQTT topic."""
        if not self.connected or not self.client:
            logger.error("MQTT client not connected")
            return False
        
        try:
            qos_level = qos or self.settings.MQTT_QOS
            json_payload = json.dumps(payload, default=str)
            
            result = self.client.publish(
                topic,
                json_payload,
                qos=qos_level,
                retain=retain
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}: {len(json_payload)} bytes")
                return True
            else:
                logger.error(f"Failed to publish to {topic}: {mqtt.error_string(result.rc)}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")
            return False
    
    async def subscribe(self, topic: str, handler: Callable, qos: Optional[int] = None) -> bool:
        """Subscribe to an MQTT topic with handler."""
        if not self.connected or not self.client:
            logger.error("MQTT client not connected")
            return False
        
        try:
            qos_level = qos or self.settings.MQTT_QOS
            result = self.client.subscribe(topic, qos_level)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.message_handlers[topic] = handler
                logger.info(f"Subscribed to MQTT topic: {topic}")
                return True
            else:
                logger.error(f"Failed to subscribe to {topic}: {mqtt.error_string(result[0])}")
                return False
                
        except Exception as e:
            logger.error(f"Error subscribing to {topic}: {e}")
            return False
    
    async def publish_device_data(self, data: Dict[str, Any]) -> bool:
        """Publish device data to the data topic."""
        topic = self.settings.get_mqtt_topic("data")
        
        # Add metadata
        payload = {
            "device_id": self.settings.DEVICE_ID,
            "device_type": self.settings.DEVICE_TYPE,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        return await self.publish(topic, payload)
    
    async def publish_device_status(self, status: Dict[str, Any]) -> bool:
        """Publish device status to the status topic."""
        topic = self.settings.get_mqtt_topic("status")
        
        payload = {
            "device_id": self.settings.DEVICE_ID,
            "device_type": self.settings.DEVICE_TYPE,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "online",
            **status
        }
        
        return await self.publish(topic, payload, retain=True)
    
    async def publish_alert(self, alert_type: str, message: str, severity: str = "warning") -> bool:
        """Publish an alert to the alerts topic."""
        topic = self.settings.get_mqtt_topic("alerts")
        
        payload = {
            "device_id": self.settings.DEVICE_ID,
            "device_type": self.settings.DEVICE_TYPE,
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": alert_type,
            "message": message,
            "severity": severity
        }
        
        return await self.publish(topic, payload)
    
    async def publish_command_response(
        self, 
        command_id: str, 
        success: bool, 
        result: Any = None,
        error: str = None
    ) -> bool:
        """Publish command execution response."""
        topic = self.settings.get_mqtt_topic("commands/response")
        
        payload = {
            "device_id": self.settings.DEVICE_ID,
            "command_id": command_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": success,
            "result": result,
            "error": error
        }
        
        return await self.publish(topic, payload)
    
    async def _publish_online_status(self) -> bool:
        """Publish online status on connection."""
        return await self.publish_device_status({
            "connection_status": "connected",
            "last_seen": datetime.utcnow().isoformat()
        })
    
    async def _publish_offline_status(self) -> bool:
        """Publish offline status before disconnection."""
        topic = self.settings.get_mqtt_topic("status")
        
        payload = {
            "device_id": self.settings.DEVICE_ID,
            "device_type": self.settings.DEVICE_TYPE,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "offline",
            "reason": "graceful_shutdown"
        }
        
        return await self.publish(topic, payload, retain=True)
    
    async def _subscribe_to_commands(self) -> bool:
        """Subscribe to command topics."""
        # Subscribe to device-specific commands
        device_command_topic = self.settings.get_mqtt_topic("commands")
        
        # Subscribe to broadcast commands
        broadcast_topic = f"{self.settings.MQTT_TOPIC_PREFIX}/broadcast/commands"
        
        success = True
        success &= await self.subscribe(device_command_topic, self._handle_command)
        success &= await self.subscribe(broadcast_topic, self._handle_command)
        
        return success
    
    async def _handle_command(self, topic: str, payload: Dict[str, Any]):
        """Handle incoming command messages."""
        try:
            command_id = payload.get("command_id")
            command_type = payload.get("command_type")
            command_data = payload.get("data", {})
            
            logger.info(f"Received command {command_id}: {command_type}")
            
            # Import here to avoid circular imports
            from command_queue import CommandQueue
            
            # Add command to queue for processing
            if hasattr(self, '_command_queue'):
                await self._command_queue.add_mqtt_command(payload)
            else:
                logger.warning("Command queue not available, ignoring command")
                
        except Exception as e:
            logger.error(f"Error handling command: {e}")
    
    def set_command_queue(self, command_queue):
        """Set reference to command queue for handling commands."""
        self._command_queue = command_queue
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of MQTT connection."""
        return {
            "connected": self.connected,
            "broker_host": self.settings.mqtt_broker_host,
            "broker_port": self.settings.mqtt_broker_port,
            "client_id": self.settings.MQTT_CLIENT_ID,
            "subscriptions": len(self.message_handlers)
        } 