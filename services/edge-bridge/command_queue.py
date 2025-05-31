"""
Command queue for serializing Modbus operations.

Critical component that ensures all Modbus commands are executed serially
to prevent concurrent access issues with the inverter firmware.
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from config import Settings

logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """Command execution status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class CommandPriority(Enum):
    """Command priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Command:
    """Modbus command definition."""
    id: str
    command_type: str
    data: Dict[str, Any]
    priority: CommandPriority = CommandPriority.NORMAL
    timeout: int = 30
    retry_count: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: CommandStatus = CommandStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    mqtt_response_topic: Optional[str] = None


class CommandQueue:
    """Thread-safe command queue with priority and retry logic."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.queue: List[Command] = []
        self.processing = False
        self.current_command: Optional[Command] = None
        self.command_history: Dict[str, Command] = {}
        self.lock = asyncio.Lock()
        
        logger.info("Command queue initialized")
    
    async def add_command(
        self, 
        command_data: Dict[str, Any],
        priority: CommandPriority = CommandPriority.NORMAL,
        timeout: int = 30
    ) -> str:
        """Add a command to the queue."""
        command_id = str(uuid.uuid4())
        
        command = Command(
            id=command_id,
            command_type=command_data.get("command_type", "unknown"),
            data=command_data,
            priority=priority,
            timeout=timeout
        )
        
        async with self.lock:
            # Check queue size limit
            if len(self.queue) >= self.settings.MAX_QUEUE_SIZE:
                raise Exception(f"Command queue full (max {self.settings.MAX_QUEUE_SIZE})")
            
            # Insert command based on priority
            self._insert_by_priority(command)
            self.command_history[command_id] = command
            
            logger.info(f"Added command {command_id} to queue (priority: {priority.name})")
        
        return command_id
    
    async def add_mqtt_command(self, mqtt_payload: Dict[str, Any]) -> str:
        """Add a command received via MQTT."""
        command_id = mqtt_payload.get("command_id", str(uuid.uuid4()))
        command_type = mqtt_payload.get("command_type")
        command_data = mqtt_payload.get("data", {})
        priority_str = mqtt_payload.get("priority", "normal").upper()
        timeout = mqtt_payload.get("timeout", 30)
        
        try:
            priority = CommandPriority[priority_str]
        except KeyError:
            priority = CommandPriority.NORMAL
        
        command = Command(
            id=command_id,
            command_type=command_type,
            data=command_data,
            priority=priority,
            timeout=timeout,
            mqtt_response_topic=mqtt_payload.get("response_topic")
        )
        
        async with self.lock:
            if len(self.queue) >= self.settings.MAX_QUEUE_SIZE:
                logger.error(f"Command queue full, rejecting command {command_id}")
                return command_id
            
            self._insert_by_priority(command)
            self.command_history[command_id] = command
            
            logger.info(f"Added MQTT command {command_id} to queue")
        
        return command_id
    
    def _insert_by_priority(self, command: Command):
        """Insert command into queue based on priority."""
        # Find insertion point based on priority
        insert_index = len(self.queue)
        for i, existing_command in enumerate(self.queue):
            if command.priority.value > existing_command.priority.value:
                insert_index = i
                break
        
        self.queue.insert(insert_index, command)
    
    async def get_next_command(self) -> Optional[Command]:
        """Get the next command from the queue."""
        async with self.lock:
            if not self.queue:
                return None
            
            # Get highest priority command
            command = self.queue.pop(0)
            self.current_command = command
            command.status = CommandStatus.PROCESSING
            command.attempts += 1
            command.last_attempt = datetime.utcnow()
            
            return command
    
    async def complete_command(self, command: Command, result: Any = None):
        """Mark command as completed."""
        async with self.lock:
            command.status = CommandStatus.COMPLETED
            command.result = result
            self.current_command = None
            
            logger.info(f"Command {command.id} completed successfully")
    
    async def fail_command(self, command: Command, error: str):
        """Mark command as failed."""
        async with self.lock:
            command.error = error
            
            # Check if we should retry
            if command.attempts < command.retry_count:
                # Re-queue for retry
                command.status = CommandStatus.PENDING
                self._insert_by_priority(command)
                logger.warning(f"Command {command.id} failed, retrying (attempt {command.attempts}/{command.retry_count})")
            else:
                command.status = CommandStatus.FAILED
                logger.error(f"Command {command.id} failed permanently: {error}")
            
            self.current_command = None
    
    async def timeout_command(self, command: Command):
        """Mark command as timed out."""
        async with self.lock:
            command.status = CommandStatus.TIMEOUT
            command.error = f"Command timed out after {command.timeout} seconds"
            self.current_command = None
            
            logger.error(f"Command {command.id} timed out")
    
    async def process_next_command(self, modbus_client):
        """Process the next command in the queue."""
        if self.processing:
            return
        
        command = await self.get_next_command()
        if not command:
            return
        
        self.processing = True
        
        try:
            # Set timeout
            timeout_task = asyncio.create_task(
                asyncio.sleep(command.timeout)
            )
            
            # Execute command
            execute_task = asyncio.create_task(
                self._execute_command(command, modbus_client)
            )
            
            # Wait for either completion or timeout
            done, pending = await asyncio.wait(
                [timeout_task, execute_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Check if command timed out
            if timeout_task in done:
                await self.timeout_command(command)
            
        except Exception as e:
            logger.error(f"Error processing command {command.id}: {e}")
            await self.fail_command(command, str(e))
        
        finally:
            self.processing = False
    
    async def _execute_command(self, command: Command, modbus_client):
        """Execute a specific command."""
        try:
            logger.info(f"Executing command {command.id}: {command.command_type}")
            
            result = None
            
            if command.command_type == "read_register":
                register_name = command.data.get("register")
                result = await modbus_client.read_register_by_name(register_name)
                
            elif command.command_type == "write_register":
                register_name = command.data.get("register")
                value = command.data.get("value")
                result = await modbus_client.write_register_by_name(register_name, value)
                
            elif command.command_type == "read_all_data":
                result = await modbus_client.read_all_data_registers()
                
            elif command.command_type == "set_charge_mode":
                enable = command.data.get("enable", True)
                result = await modbus_client.write_register_by_name("enable_charge", 1 if enable else 0)
                
            elif command.command_type == "set_discharge_mode":
                enable = command.data.get("enable", True)
                result = await modbus_client.write_register_by_name("enable_discharge", 1 if enable else 0)
                
            elif command.command_type == "set_charge_power":
                power = command.data.get("power")
                result = await modbus_client.write_register_by_name("charge_power_limit", power)
                
            elif command.command_type == "set_discharge_power":
                power = command.data.get("power")
                result = await modbus_client.write_register_by_name("discharge_power_limit", power)
                
            elif command.command_type == "set_charge_schedule":
                start_time = command.data.get("start_time")
                end_time = command.data.get("end_time")
                slot = command.data.get("slot", 1)
                
                if slot == 1:
                    await modbus_client.write_register_by_name("charge_time_1_start", start_time)
                    result = await modbus_client.write_register_by_name("charge_time_1_end", end_time)
                else:
                    await modbus_client.write_register_by_name("charge_time_2_start", start_time)
                    result = await modbus_client.write_register_by_name("charge_time_2_end", end_time)
                
            elif command.command_type == "set_discharge_schedule":
                start_time = command.data.get("start_time")
                end_time = command.data.get("end_time")
                slot = command.data.get("slot", 1)
                
                if slot == 1:
                    await modbus_client.write_register_by_name("discharge_time_1_start", start_time)
                    result = await modbus_client.write_register_by_name("discharge_time_1_end", end_time)
                else:
                    await modbus_client.write_register_by_name("discharge_time_2_start", start_time)
                    result = await modbus_client.write_register_by_name("discharge_time_2_end", end_time)
                
            else:
                raise Exception(f"Unknown command type: {command.command_type}")
            
            await self.complete_command(command, result)
            
        except Exception as e:
            await self.fail_command(command, str(e))
    
    async def get_command_status(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific command."""
        command = self.command_history.get(command_id)
        if not command:
            return None
        
        return {
            "command_id": command.id,
            "command_type": command.command_type,
            "status": command.status.value,
            "priority": command.priority.name,
            "created_at": command.created_at.isoformat(),
            "attempts": command.attempts,
            "last_attempt": command.last_attempt.isoformat() if command.last_attempt else None,
            "result": command.result,
            "error": command.error
        }
    
    def size(self) -> int:
        """Get current queue size."""
        return len(self.queue)
    
    def is_processing(self) -> bool:
        """Check if currently processing a command."""
        return self.processing
    
    async def cancel_command(self, command_id: str) -> bool:
        """Cancel a pending command."""
        async with self.lock:
            # Find and remove from queue
            for i, command in enumerate(self.queue):
                if command.id == command_id:
                    command.status = CommandStatus.CANCELLED
                    self.queue.pop(i)
                    logger.info(f"Cancelled command {command_id}")
                    return True
            
            return False
    
    async def clear_queue(self):
        """Clear all pending commands."""
        async with self.lock:
            cancelled_count = len(self.queue)
            for command in self.queue:
                command.status = CommandStatus.CANCELLED
            self.queue.clear()
            
            logger.info(f"Cleared {cancelled_count} commands from queue")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status."""
        status_counts = {}
        for command in self.command_history.values():
            status = command.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "queue_size": len(self.queue),
            "processing": self.processing,
            "current_command": self.current_command.id if self.current_command else None,
            "total_commands": len(self.command_history),
            "status_counts": status_counts
        } 