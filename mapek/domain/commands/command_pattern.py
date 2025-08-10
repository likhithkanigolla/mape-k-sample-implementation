"""
Command Pattern Implementation for Reversible Operations in Digital Twin
Enables undo/redo functionality and operation history for water utility management.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
import json
from uuid import uuid4
import copy

logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """Status of command execution."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNDONE = "undone"
    ROLLED_BACK = "rolled_back"


class CommandPriority(Enum):
    """Priority levels for command execution."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    side_effects: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "execution_time_ms": self.execution_time_ms,
            "side_effects": self.side_effects
        }


class Command(ABC):
    """Abstract base class for all commands in the digital twin system."""
    
    def __init__(self, command_id: Optional[str] = None, priority: CommandPriority = CommandPriority.NORMAL):
        self.command_id = command_id or str(uuid4())
        self.priority = priority
        self.status = CommandStatus.PENDING
        self.created_at = datetime.now()
        self.executed_at: Optional[datetime] = None
        self.undone_at: Optional[datetime] = None
        self.metadata: Dict[str, Any] = {}
        self.prerequisites: List['Command'] = []
        self.dependents: List['Command'] = []
        self.rollback_data: Dict[str, Any] = {}
    
    @abstractmethod
    async def execute(self) -> CommandResult:
        """Execute the command."""
        pass
    
    @abstractmethod
    async def undo(self) -> CommandResult:
        """Undo the command (reverse its effects)."""
        pass
    
    @abstractmethod
    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        pass
    
    def get_description(self) -> str:
        """Get human-readable description of the command."""
        return f"{self.__class__.__name__}(id={self.command_id[:8]})"
    
    def add_prerequisite(self, command: 'Command') -> None:
        """Add a prerequisite command that must execute before this one."""
        self.prerequisites.append(command)
        command.dependents.append(self)
    
    def can_execute(self) -> bool:
        """Check if all prerequisites are satisfied."""
        return all(cmd.status == CommandStatus.COMPLETED for cmd in self.prerequisites)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata for the command."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata for the command."""
        return self.metadata.get(key, default)


class SystemParameterAdjustmentCommand(Command):
    """Command to adjust system parameters (pressure, flow, etc.)."""
    
    def __init__(self, parameter_name: str, new_value: float, target_component: str,
                 command_id: Optional[str] = None, priority: CommandPriority = CommandPriority.NORMAL):
        super().__init__(command_id, priority)
        self.parameter_name = parameter_name
        self.new_value = new_value
        self.target_component = target_component
        self.previous_value: Optional[float] = None
        self.adjustment_rate = 0.1  # Rate of change per second
        self.safety_limits = self._get_safety_limits()
    
    def _get_safety_limits(self) -> Dict[str, tuple]:
        """Get safety limits for different parameters."""
        limits = {
            "pressure": (0.0, 6.0),  # bar
            "flow_rate": (0.0, 200.0),  # L/min
            "valve_position": (0.0, 100.0),  # percentage
            "pump_speed": (0.0, 100.0),  # percentage
            "temperature": (-5.0, 50.0),  # Celsius
        }
        return limits.get(self.parameter_name, (float('-inf'), float('inf')))
    
    async def execute(self) -> CommandResult:
        """Execute the parameter adjustment."""
        start_time = datetime.now()
        
        try:
            # Check safety limits
            min_val, max_val = self.safety_limits
            if not (min_val <= self.new_value <= max_val):
                return CommandResult(
                    success=False,
                    message=f"Value {self.new_value} outside safety limits [{min_val}, {max_val}]",
                    execution_time_ms=0.0
                )
            
            # Store current value for rollback
            self.previous_value = await self._get_current_value()
            
            # Perform gradual adjustment to prevent system shock
            current_value = self.previous_value
            steps = max(1, int(abs(self.new_value - current_value) / self.adjustment_rate))
            step_size = (self.new_value - current_value) / steps
            
            for i in range(steps):
                intermediate_value = current_value + (step_size * (i + 1))
                await self._set_parameter_value(intermediate_value)
                await asyncio.sleep(0.1)  # Small delay between steps
            
            # Verify final value
            final_value = await self._get_current_value()
            
            self.status = CommandStatus.COMPLETED
            self.executed_at = datetime.now()
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"Adjusted {self.parameter_name} on {self.target_component} "
                       f"from {self.previous_value} to {final_value}")
            
            return CommandResult(
                success=True,
                message=f"Successfully adjusted {self.parameter_name} to {final_value}",
                data={
                    "parameter": self.parameter_name,
                    "component": self.target_component,
                    "previous_value": self.previous_value,
                    "new_value": final_value,
                    "steps_taken": steps
                },
                execution_time_ms=execution_time,
                side_effects=[f"Component {self.target_component} parameter changed"]
            )
            
        except Exception as e:
            self.status = CommandStatus.FAILED
            logger.error(f"Failed to execute parameter adjustment: {e}")
            
            return CommandResult(
                success=False,
                message=f"Failed to adjust {self.parameter_name}: {str(e)}",
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def undo(self) -> CommandResult:
        """Undo the parameter adjustment by restoring previous value."""
        if self.previous_value is None:
            return CommandResult(
                success=False,
                message="Cannot undo: no previous value stored"
            )
        
        start_time = datetime.now()
        
        try:
            # Gradually restore previous value
            current_value = await self._get_current_value()
            steps = max(1, int(abs(self.previous_value - current_value) / self.adjustment_rate))
            step_size = (self.previous_value - current_value) / steps
            
            for i in range(steps):
                intermediate_value = current_value + (step_size * (i + 1))
                await self._set_parameter_value(intermediate_value)
                await asyncio.sleep(0.1)
            
            final_value = await self._get_current_value()
            
            self.status = CommandStatus.UNDONE
            self.undone_at = datetime.now()
            
            logger.info(f"Undid adjustment of {self.parameter_name} on {self.target_component} "
                       f"restored to {final_value}")
            
            return CommandResult(
                success=True,
                message=f"Successfully undid {self.parameter_name} adjustment",
                data={
                    "parameter": self.parameter_name,
                    "component": self.target_component,
                    "restored_value": final_value
                },
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            logger.error(f"Failed to undo parameter adjustment: {e}")
            return CommandResult(
                success=False,
                message=f"Failed to undo {self.parameter_name} adjustment: {str(e)}"
            )
    
    def can_undo(self) -> bool:
        """Check if this command can be undone."""
        return (self.status == CommandStatus.COMPLETED and 
                self.previous_value is not None)
    
    async def _get_current_value(self) -> float:
        """Get current parameter value (simulation)."""
        # In real implementation, this would query the actual system
        return 2.5  # Simulated current value
    
    async def _set_parameter_value(self, value: float) -> None:
        """Set parameter value (simulation)."""
        # In real implementation, this would send commands to the actual system
        await asyncio.sleep(0.01)  # Simulate network delay
        logger.debug(f"Set {self.parameter_name} on {self.target_component} to {value}")


class EmergencyShutdownCommand(Command):
    """Command to perform emergency shutdown of system components."""
    
    def __init__(self, component_ids: List[str], reason: str,
                 command_id: Optional[str] = None):
        super().__init__(command_id, CommandPriority.EMERGENCY)
        self.component_ids = component_ids
        self.reason = reason
        self.component_states: Dict[str, Dict[str, Any]] = {}
    
    async def execute(self) -> CommandResult:
        """Execute emergency shutdown."""
        start_time = datetime.now()
        
        try:
            # Store current states for potential restoration
            for component_id in self.component_ids:
                self.component_states[component_id] = await self._get_component_state(component_id)
            
            # Perform shutdown
            shutdown_results = []
            for component_id in self.component_ids:
                result = await self._shutdown_component(component_id)
                shutdown_results.append(result)
            
            self.status = CommandStatus.COMPLETED
            self.executed_at = datetime.now()
            
            logger.critical(f"Emergency shutdown completed for components: {self.component_ids}")
            
            return CommandResult(
                success=True,
                message=f"Emergency shutdown completed for {len(self.component_ids)} components",
                data={
                    "components_shutdown": self.component_ids,
                    "reason": self.reason,
                    "shutdown_results": shutdown_results
                },
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                side_effects=[f"Components {', '.join(self.component_ids)} shut down"]
            )
            
        except Exception as e:
            self.status = CommandStatus.FAILED
            logger.error(f"Emergency shutdown failed: {e}")
            
            return CommandResult(
                success=False,
                message=f"Emergency shutdown failed: {str(e)}"
            )
    
    async def undo(self) -> CommandResult:
        """Restore components to their previous states."""
        if not self.component_states:
            return CommandResult(
                success=False,
                message="Cannot undo: no component states stored"
            )
        
        start_time = datetime.now()
        
        try:
            restore_results = []
            for component_id, previous_state in self.component_states.items():
                result = await self._restore_component(component_id, previous_state)
                restore_results.append(result)
            
            self.status = CommandStatus.UNDONE
            self.undone_at = datetime.now()
            
            logger.info(f"Restored components from emergency shutdown: {self.component_ids}")
            
            return CommandResult(
                success=True,
                message=f"Restored {len(self.component_ids)} components from shutdown",
                data={
                    "components_restored": self.component_ids,
                    "restore_results": restore_results
                },
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            logger.error(f"Failed to restore from emergency shutdown: {e}")
            return CommandResult(
                success=False,
                message=f"Failed to restore components: {str(e)}"
            )
    
    def can_undo(self) -> bool:
        """Emergency shutdown can be undone if component states were stored."""
        return (self.status == CommandStatus.COMPLETED and 
                bool(self.component_states))
    
    async def _get_component_state(self, component_id: str) -> Dict[str, Any]:
        """Get current state of a component."""
        # Simulation of component state
        return {
            "active": True,
            "parameters": {"pressure": 3.0, "flow_rate": 50.0},
            "last_maintenance": "2024-01-01"
        }
    
    async def _shutdown_component(self, component_id: str) -> Dict[str, Any]:
        """Shutdown a component."""
        await asyncio.sleep(0.1)  # Simulate shutdown time
        return {"component_id": component_id, "shutdown_success": True}
    
    async def _restore_component(self, component_id: str, previous_state: Dict[str, Any]) -> Dict[str, Any]:
        """Restore a component to its previous state."""
        await asyncio.sleep(0.2)  # Simulate restoration time
        return {"component_id": component_id, "restore_success": True, "state": previous_state}


class CompositeCommand(Command):
    """Command that executes multiple sub-commands as a single unit."""
    
    def __init__(self, sub_commands: List[Command], command_id: Optional[str] = None,
                 priority: CommandPriority = CommandPriority.NORMAL):
        super().__init__(command_id, priority)
        self.sub_commands = sub_commands
        self.executed_commands: List[Command] = []
        self.execution_strategy = "sequential"  # or "parallel"
    
    async def execute(self) -> CommandResult:
        """Execute all sub-commands."""
        start_time = datetime.now()
        results = []
        
        try:
            if self.execution_strategy == "sequential":
                for cmd in self.sub_commands:
                    result = await cmd.execute()
                    results.append(result)
                    self.executed_commands.append(cmd)
                    
                    if not result.success:
                        # If any command fails, stop and rollback
                        await self._rollback_executed_commands()
                        return CommandResult(
                            success=False,
                            message=f"Composite command failed at {cmd.get_description()}: {result.message}",
                            data={"partial_results": results}
                        )
            
            elif self.execution_strategy == "parallel":
                tasks = [cmd.execute() for cmd in self.sub_commands]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check for any failures
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        return CommandResult(
                            success=False,
                            message=f"Parallel execution failed: {str(result)}"
                        )
                    elif not result.success:
                        await self._rollback_all_commands()
                        return CommandResult(
                            success=False,
                            message=f"Composite command failed: {result.message}",
                            data={"all_results": [r.to_dict() if hasattr(r, 'to_dict') else str(r) for r in results]}
                        )
            
            self.status = CommandStatus.COMPLETED
            self.executed_at = datetime.now()
            
            return CommandResult(
                success=True,
                message=f"Successfully executed {len(self.sub_commands)} sub-commands",
                data={
                    "sub_command_results": [r.to_dict() if hasattr(r, 'to_dict') else str(r) for r in results],
                    "execution_strategy": self.execution_strategy
                },
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            await self._rollback_executed_commands()
            self.status = CommandStatus.FAILED
            
            return CommandResult(
                success=False,
                message=f"Composite command failed with exception: {str(e)}"
            )
    
    async def undo(self) -> CommandResult:
        """Undo all executed sub-commands in reverse order."""
        if not self.executed_commands:
            return CommandResult(
                success=False,
                message="No sub-commands to undo"
            )
        
        # Undo in reverse order
        undo_results = []
        for cmd in reversed(self.executed_commands):
            if cmd.can_undo():
                result = await cmd.undo()
                undo_results.append(result)
                
                if not result.success:
                    logger.error(f"Failed to undo sub-command {cmd.get_description()}")
        
        self.status = CommandStatus.UNDONE
        self.undone_at = datetime.now()
        
        return CommandResult(
            success=True,
            message=f"Undid {len(undo_results)} sub-commands",
            data={"undo_results": [r.to_dict() for r in undo_results]}
        )
    
    def can_undo(self) -> bool:
        """Composite command can be undone if any sub-commands can be undone."""
        return any(cmd.can_undo() for cmd in self.executed_commands)
    
    async def _rollback_executed_commands(self) -> None:
        """Rollback all executed commands in reverse order."""
        for cmd in reversed(self.executed_commands):
            if cmd.can_undo():
                await cmd.undo()
    
    async def _rollback_all_commands(self) -> None:
        """Rollback all sub-commands."""
        for cmd in reversed(self.sub_commands):
            if cmd.can_undo():
                await cmd.undo()


class CommandInvoker:
    """Invoker class that manages command execution, history, and undo/redo operations."""
    
    def __init__(self, max_history_size: int = 1000):
        self.command_history: List[Command] = []
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_history_size = max_history_size
        self.active_commands: Dict[str, Command] = {}
    
    async def execute_command(self, command: Command) -> CommandResult:
        """Execute a command and add it to history."""
        # Check if command can be executed
        if not command.can_execute():
            return CommandResult(
                success=False,
                message="Command prerequisites not satisfied"
            )
        
        # Add to active commands
        self.active_commands[command.command_id] = command
        command.status = CommandStatus.EXECUTING
        
        try:
            # Execute the command
            result = await command.execute()
            
            if result.success:
                # Add to history and undo stack
                self.command_history.append(command)
                if command.can_undo():
                    self.undo_stack.append(command)
                    # Clear redo stack when new command is executed
                    self.redo_stack.clear()
                
                # Maintain history size limit
                if len(self.command_history) > self.max_history_size:
                    self.command_history.pop(0)
                
                logger.info(f"Command executed successfully: {command.get_description()}")
            else:
                logger.error(f"Command execution failed: {command.get_description()}")
            
            return result
            
        except Exception as e:
            command.status = CommandStatus.FAILED
            logger.error(f"Command execution exception: {e}")
            return CommandResult(
                success=False,
                message=f"Command execution failed with exception: {str(e)}"
            )
        
        finally:
            # Remove from active commands
            self.active_commands.pop(command.command_id, None)
    
    async def undo_last_command(self) -> CommandResult:
        """Undo the last executed command."""
        if not self.undo_stack:
            return CommandResult(
                success=False,
                message="No commands to undo"
            )
        
        command = self.undo_stack.pop()
        
        try:
            result = await command.undo()
            
            if result.success:
                self.redo_stack.append(command)
                logger.info(f"Command undone: {command.get_description()}")
            else:
                # Put back on undo stack if undo failed
                self.undo_stack.append(command)
                logger.error(f"Failed to undo command: {command.get_description()}")
            
            return result
            
        except Exception as e:
            self.undo_stack.append(command)  # Put back on stack
            logger.error(f"Undo operation failed: {e}")
            return CommandResult(
                success=False,
                message=f"Undo failed with exception: {str(e)}"
            )
    
    async def redo_last_command(self) -> CommandResult:
        """Redo the last undone command."""
        if not self.redo_stack:
            return CommandResult(
                success=False,
                message="No commands to redo"
            )
        
        command = self.redo_stack.pop()
        
        try:
            result = await command.execute()
            
            if result.success:
                self.undo_stack.append(command)
                logger.info(f"Command redone: {command.get_description()}")
            else:
                # Put back on redo stack if redo failed
                self.redo_stack.append(command)
                logger.error(f"Failed to redo command: {command.get_description()}")
            
            return result
            
        except Exception as e:
            self.redo_stack.append(command)  # Put back on stack
            logger.error(f"Redo operation failed: {e}")
            return CommandResult(
                success=False,
                message=f"Redo failed with exception: {str(e)}"
            )
    
    def get_command_history(self) -> List[Dict[str, Any]]:
        """Get command execution history."""
        return [
            {
                "command_id": cmd.command_id,
                "description": cmd.get_description(),
                "status": cmd.status.value,
                "created_at": cmd.created_at.isoformat(),
                "executed_at": cmd.executed_at.isoformat() if cmd.executed_at else None,
                "priority": cmd.priority.value,
                "can_undo": cmd.can_undo()
            }
            for cmd in self.command_history
        ]
    
    def get_undo_stack_info(self) -> List[str]:
        """Get information about commands that can be undone."""
        return [cmd.get_description() for cmd in self.undo_stack]
    
    def get_redo_stack_info(self) -> List[str]:
        """Get information about commands that can be redone."""
        return [cmd.get_description() for cmd in self.redo_stack]
    
    def get_active_commands(self) -> Dict[str, str]:
        """Get currently executing commands."""
        return {
            cmd_id: cmd.get_description()
            for cmd_id, cmd in self.active_commands.items()
        }
    
    async def cancel_command(self, command_id: str) -> CommandResult:
        """Cancel an active command (if supported)."""
        if command_id not in self.active_commands:
            return CommandResult(
                success=False,
                message=f"Command {command_id} is not active"
            )
        
        # For now, we don't implement command cancellation
        # In a real system, this would involve interrupting the command execution
        return CommandResult(
            success=False,
            message="Command cancellation not implemented"
        )


# Global command invoker instance
global_command_invoker = CommandInvoker()


# Command factory for creating common commands
class CommandFactory:
    """Factory for creating commonly used commands."""
    
    @staticmethod
    def create_pressure_adjustment(component_id: str, new_pressure: float) -> SystemParameterAdjustmentCommand:
        """Create a pressure adjustment command."""
        return SystemParameterAdjustmentCommand(
            parameter_name="pressure",
            new_value=new_pressure,
            target_component=component_id,
            priority=CommandPriority.HIGH
        )
    
    @staticmethod
    def create_flow_adjustment(component_id: str, new_flow_rate: float) -> SystemParameterAdjustmentCommand:
        """Create a flow rate adjustment command."""
        return SystemParameterAdjustmentCommand(
            parameter_name="flow_rate",
            new_value=new_flow_rate,
            target_component=component_id,
            priority=CommandPriority.NORMAL
        )
    
    @staticmethod
    def create_emergency_shutdown(component_ids: List[str], reason: str) -> EmergencyShutdownCommand:
        """Create an emergency shutdown command."""
        return EmergencyShutdownCommand(
            component_ids=component_ids,
            reason=reason
        )
    
    @staticmethod
    def create_system_optimization_sequence(target_pressure: float, target_flow: float) -> CompositeCommand:
        """Create a composite command for system optimization."""
        pressure_cmd = CommandFactory.create_pressure_adjustment("main_pump", target_pressure)
        flow_cmd = CommandFactory.create_flow_adjustment("main_valve", target_flow)
        
        # Set dependency: pressure adjustment must complete before flow adjustment
        flow_cmd.add_prerequisite(pressure_cmd)
        
        return CompositeCommand(
            sub_commands=[pressure_cmd, flow_cmd],
            priority=CommandPriority.HIGH
        )
