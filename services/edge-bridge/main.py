"""
Nattery Edge Bridge Service

Critical hardware communication bridge between Modbus RTU inverter and MQTT broker.
Handles serialized command execution and real-time data publishing.

Architecture: Inverter ← Modbus RTU ← USB Converter ← Raspberry Pi ← MQTT ← Services
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from config import Settings
from modbus_client import ModbusClient
from mqtt_client import MQTTClient
from command_queue import CommandQueue
from data_publisher import DataPublisher
from health_monitor import HealthMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
settings = Settings()
modbus_client: ModbusClient = None
mqtt_client: MQTTClient = None
command_queue: CommandQueue = None
data_publisher: DataPublisher = None
health_monitor: HealthMonitor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global modbus_client, mqtt_client, command_queue, data_publisher, health_monitor
    
    logger.info("Starting Nattery Edge Bridge Service...")
    
    try:
        # Initialize components
        modbus_client = ModbusClient(settings)
        mqtt_client = MQTTClient(settings)
        command_queue = CommandQueue()
        data_publisher = DataPublisher(mqtt_client, settings)
        health_monitor = HealthMonitor(modbus_client, mqtt_client)
        
        # Connect to MQTT broker
        await mqtt_client.connect()
        logger.info("Connected to MQTT broker")
        
        # Connect to Modbus device
        await modbus_client.connect()
        logger.info("Connected to Modbus device")
        
        # Start background tasks
        asyncio.create_task(command_processor())
        asyncio.create_task(data_collection_loop())
        asyncio.create_task(health_check_loop())
        
        logger.info("Edge Bridge Service started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Edge Bridge Service: {e}")
        raise
    
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down Edge Bridge Service...")
        
        if mqtt_client:
            await mqtt_client.disconnect()
        
        if modbus_client:
            await modbus_client.disconnect()
        
        logger.info("Edge Bridge Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Nattery Edge Bridge Service",
    description="Hardware communication bridge for battery energy trading system",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for monitoring."""
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    health_status = await health_monitor.get_health_status()
    
    if health_status["status"] == "healthy":
        return health_status
    else:
        raise HTTPException(status_code=503, detail=health_status)


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get detailed service status."""
    if not all([modbus_client, mqtt_client, command_queue]):
        raise HTTPException(status_code=503, detail="Service not fully initialized")
    
    return {
        "service": "edge-bridge",
        "version": "1.0.0",
        "modbus": {
            "connected": modbus_client.is_connected(),
            "port": settings.MODBUS_PORT,
            "slave_id": settings.MODBUS_SLAVE_ID
        },
        "mqtt": {
            "connected": mqtt_client.is_connected(),
            "broker": settings.MQTT_BROKER_URL
        },
        "command_queue": {
            "pending_commands": command_queue.size(),
            "processing": command_queue.is_processing()
        }
    }


@app.post("/commands")
async def execute_command(
    command: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """Execute a Modbus command (queued for serialization)."""
    if not command_queue:
        raise HTTPException(status_code=503, detail="Command queue not initialized")
    
    try:
        command_id = await command_queue.add_command(command)
        return {
            "command_id": command_id,
            "status": "queued",
            "message": "Command added to queue for execution"
        }
    except Exception as e:
        logger.error(f"Failed to queue command: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/commands/{command_id}")
async def get_command_status(command_id: str) -> Dict[str, Any]:
    """Get status of a specific command."""
    if not command_queue:
        raise HTTPException(status_code=503, detail="Command queue not initialized")
    
    status = await command_queue.get_command_status(command_id)
    if not status:
        raise HTTPException(status_code=404, detail="Command not found")
    
    return status


async def command_processor():
    """Background task to process commands from the queue."""
    logger.info("Starting command processor...")
    
    while True:
        try:
            if command_queue and modbus_client:
                await command_queue.process_next_command(modbus_client)
            await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
        except Exception as e:
            logger.error(f"Error in command processor: {e}")
            await asyncio.sleep(1)  # Longer delay on error


async def data_collection_loop():
    """Background task to collect data from Modbus and publish to MQTT."""
    logger.info("Starting data collection loop...")
    
    while True:
        try:
            if modbus_client and data_publisher:
                await data_publisher.collect_and_publish(modbus_client)
            await asyncio.sleep(settings.DATA_COLLECTION_INTERVAL)
        except Exception as e:
            logger.error(f"Error in data collection: {e}")
            await asyncio.sleep(5)  # Longer delay on error


async def health_check_loop():
    """Background task for periodic health checks."""
    logger.info("Starting health check loop...")
    
    while True:
        try:
            if health_monitor:
                await health_monitor.perform_health_check()
            await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            await asyncio.sleep(10)  # Longer delay on error


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.PYTHON_ENV == "development"
    ) 