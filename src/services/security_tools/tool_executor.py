"""Core tool execution engine for security tools integration."""

import asyncio
import json
import logging
import os
import shlex
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class ToolStatus(str, Enum):
    """Tool execution status."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"


class ToolCategory(str, Enum):
    """Security tool categories."""
    NETWORK_SCANNING = "NETWORK_SCANNING"
    VULNERABILITY_SCANNING = "VULNERABILITY_SCANNING"
    WEB_SECURITY = "WEB_SECURITY"
    WIRELESS = "WIRELESS"
    EXPLOITATION = "EXPLOITATION"
    PASSWORD_ATTACK = "PASSWORD_ATTACK"
    FORENSICS = "FORENSICS"
    REVERSE_ENGINEERING = "REVERSE_ENGINEERING"
    SOCIAL_ENGINEERING = "SOCIAL_ENGINEERING"
    SNIFFING = "SNIFFING"


@dataclass
class ToolConfig:
    """Configuration for a security tool."""
    
    name: str
    category: ToolCategory
    command: str
    docker_image: str | None = None
    requires_root: bool = False
    timeout_seconds: int = 300
    max_memory_mb: int = 1024
    max_cpu_percent: int = 80
    network_access: bool = True
    filesystem_access: bool = False
    environment_vars: dict[str, str] = field(default_factory=dict)
    allowed_args: list[str] = field(default_factory=list)
    dangerous_args: list[str] = field(default_factory=list)


@dataclass
class ToolExecution:
    """Represents a tool execution instance."""
    
    execution_id: str
    tool_name: str
    category: ToolCategory
    command: str
    args: list[str]
    status: ToolStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    output_files: list[str] = field(default_factory=list)
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolExecutor:
    """Core engine for executing security tools safely."""
    
    def __init__(self, use_docker: bool = True, workspace_dir: str = "/tmp/security_tools"):
        """Initialize tool executor.
        
        Args:
            use_docker: Whether to use Docker for isolation
            workspace_dir: Directory for tool outputs
        """
        self.use_docker = use_docker
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Active executions
        self.executions: dict[str, ToolExecution] = {}
        
        # Resource limits
        self.max_concurrent_executions = 10
        self.global_timeout = 3600  # 1 hour max
    
    async def execute_tool(
        self,
        tool_config: ToolConfig,
        args: list[str],
        target: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> ToolExecution:
        """Execute a security tool with safety checks.
        
        Args:
            tool_config: Tool configuration
            args: Command-line arguments
            target: Target IP/domain/URL
            options: Additional execution options
        
        Returns:
            ToolExecution instance
        """
        execution_id = str(uuid4())
        options = options or {}
        
        # Create execution record
        execution = ToolExecution(
            execution_id=execution_id,
            tool_name=tool_config.name,
            category=tool_config.category,
            command=tool_config.command,
            args=args,
            status=ToolStatus.PENDING,
            metadata={
                "target": target,
                "use_docker": self.use_docker,
                "options": options,
            },
        )
        
        self.executions[execution_id] = execution
        
        try:
            # Validate inputs
            self._validate_execution(tool_config, args, target)
            
            # Check resource limits
            await self._check_resource_limits()
            
            # Prepare execution environment
            work_dir = self._prepare_workspace(execution_id)
            
            # Build command
            if self.use_docker and tool_config.docker_image:
                command = self._build_docker_command(tool_config, args, work_dir, target)
            else:
                command = self._build_direct_command(tool_config, args, target)
            
            # Execute
            execution.status = ToolStatus.RUNNING
            execution.started_at = utcnow()
            
            logger.info(f"Executing {tool_config.name} (ID: {execution_id})")
            
            result = await self._run_command(
                command,
                timeout=tool_config.timeout_seconds,
                work_dir=work_dir,
                env=tool_config.environment_vars,
            )
            
            # Process results
            execution.stdout = result["stdout"]
            execution.stderr = result["stderr"]
            execution.exit_code = result["exit_code"]
            execution.completed_at = utcnow()
            
            if result["exit_code"] == 0:
                execution.status = ToolStatus.COMPLETED
                logger.info(f"Tool execution completed successfully: {execution_id}")
            else:
                execution.status = ToolStatus.FAILED
                execution.error_message = f"Exit code: {result['exit_code']}"
                logger.warning(f"Tool execution failed: {execution_id}")
            
            # Collect output files
            execution.output_files = self._collect_output_files(work_dir)
            
        except asyncio.TimeoutError:
            execution.status = ToolStatus.TIMEOUT
            execution.completed_at = utcnow()
            execution.error_message = "Execution timeout"
            logger.error(f"Tool execution timeout: {execution_id}")
            
        except Exception as e:
            execution.status = ToolStatus.FAILED
            execution.completed_at = utcnow()
            execution.error_message = str(e)
            logger.exception(f"Tool execution error: {execution_id}")
        
        return execution
    
    def _validate_execution(
        self,
        tool_config: ToolConfig,
        args: list[str],
        target: str | None,
    ) -> None:
        """Validate tool execution parameters.
        
        Raises:
            ValueError: If validation fails
        """
        # Check for dangerous arguments
        for arg in args:
            for dangerous in tool_config.dangerous_args:
                if dangerous.lower() in arg.lower():
                    raise ValueError(f"Dangerous argument detected: {arg}")
        
        # Validate target format
        if target:
            self._validate_target(target)
        
        # Check allowed arguments
        if tool_config.allowed_args:
            for arg in args:
                arg_name = arg.split("=")[0].lstrip("-")
                if arg_name not in tool_config.allowed_args:
                    raise ValueError(f"Argument not allowed: {arg}")
    
    def _validate_target(self, target: str) -> None:
        """Validate target address/URL.
        
        Raises:
            ValueError: If target is invalid
        """
        import re
        
        # Prevent command injection
        if any(char in target for char in [";", "|", "&", "$", "`", "\n", "\r"]):
            raise ValueError("Invalid characters in target")
        
        # Validate IP address
        ip_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        
        # Validate domain
        domain_pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        
        # Validate URL
        url_pattern = r"^https?://[^\s]+$"
        
        if not (re.match(ip_pattern, target) or 
                re.match(domain_pattern, target) or 
                re.match(url_pattern, target)):
            raise ValueError(f"Invalid target format: {target}")
    
    async def _check_resource_limits(self) -> None:
        """Check if system resources are available.
        
        Raises:
            RuntimeError: If resource limits exceeded
        """
        running_count = sum(
            1 for e in self.executions.values() 
            if e.status == ToolStatus.RUNNING
        )
        
        if running_count >= self.max_concurrent_executions:
            raise RuntimeError("Maximum concurrent executions reached")
    
    def _prepare_workspace(self, execution_id: str) -> Path:
        """Prepare workspace directory for execution.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            Path to workspace directory
        """
        work_dir = self.workspace_dir / execution_id
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir
    
    def _build_docker_command(
        self,
        tool_config: ToolConfig,
        args: list[str],
        work_dir: Path,
        target: str | None,
    ) -> list[str]:
        """Build Docker command for tool execution.
        
        Args:
            tool_config: Tool configuration
            args: Command arguments
            work_dir: Workspace directory
            target: Target address
        
        Returns:
            Docker command as list
        """
        cmd = [
            "docker", "run",
            "--rm",  # Remove container after execution
            "--network", "bridge" if tool_config.network_access else "none",
            "--memory", f"{tool_config.max_memory_mb}m",
            "--cpus", str(tool_config.max_cpu_percent / 100),
            "-v", f"{work_dir}:/output",
            "-w", "/output",
        ]
        
        # Add environment variables
        for key, value in tool_config.environment_vars.items():
            cmd.extend(["-e", f"{key}={value}"])
        
        # Add image and command
        cmd.append(tool_config.docker_image)
        cmd.append(tool_config.command)
        
        # Add arguments
        cmd.extend(args)
        
        # Add target if provided
        if target:
            cmd.append(target)
        
        return cmd
    
    def _build_direct_command(
        self,
        tool_config: ToolConfig,
        args: list[str],
        target: str | None,
    ) -> list[str]:
        """Build direct command for tool execution.
        
        Args:
            tool_config: Tool configuration
            args: Command arguments
            target: Target address
        
        Returns:
            Command as list
        """
        cmd = [tool_config.command]
        cmd.extend(args)
        
        if target:
            cmd.append(target)
        
        return cmd
    
    async def _run_command(
        self,
        command: list[str],
        timeout: int,
        work_dir: Path,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Run command and capture output.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            work_dir: Working directory
            env: Environment variables
        
        Returns:
            Execution result
        """
        try:
            # Prepare environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(work_dir),
                env=exec_env,
            )
            
            # Wait with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }
            
        except asyncio.TimeoutError:
            # Kill process if timeout
            try:
                process.kill()
                await process.wait()
            except:
                pass
            raise
    
    def _collect_output_files(self, work_dir: Path) -> list[str]:
        """Collect output files from workspace.
        
        Args:
            work_dir: Workspace directory
        
        Returns:
            List of output file paths
        """
        output_files = []
        
        if work_dir.exists():
            for file_path in work_dir.rglob("*"):
                if file_path.is_file():
                    output_files.append(str(file_path.relative_to(work_dir)))
        
        return output_files
    
    def get_execution(self, execution_id: str) -> ToolExecution | None:
        """Get execution by ID.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            ToolExecution if found, None otherwise
        """
        return self.executions.get(execution_id)
    
    def list_executions(
        self,
        status: ToolStatus | None = None,
        category: ToolCategory | None = None,
    ) -> list[ToolExecution]:
        """List executions with optional filters.
        
        Args:
            status: Filter by status
            category: Filter by category
        
        Returns:
            List of matching executions
        """
        executions = list(self.executions.values())
        
        if status:
            executions = [e for e in executions if e.status == status]
        
        if category:
            executions = [e for e in executions if e.category == category]
        
        return executions
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel running execution.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            True if cancelled, False otherwise
        """
        execution = self.executions.get(execution_id)
        
        if not execution or execution.status != ToolStatus.RUNNING:
            return False
        
        # TODO: Implement process killing
        execution.status = ToolStatus.CANCELLED
        execution.completed_at = utcnow()
        
        return True


# Global instance
_tool_executor: ToolExecutor | None = None


def get_tool_executor() -> ToolExecutor:
    """Get tool executor instance."""
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor()
    return _tool_executor
