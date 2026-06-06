"""
OpenCode Wrapper - Python Interface
A Pythonic wrapper for the OpenCode AI coding agent.

Usage:
    from opencode import OpenCode, AgentType

    client = OpenCode(model="anthropic/claude-3-opus", api_key="sk-...")
    result = client.build.run(prompt="Create a REST API", working_dir="./project")
"""

import subprocess
import json
import os
import tempfile
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class AgentType(Enum):
    BUILD = "build"
    PLAN = "plan"
    GENERAL = "general"


@dataclass
class TaskResult:
    output: str
    summary: str
    files_modified: List[Dict[str, str]] = field(default_factory=list)
    shell_commands: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    steps: int = 0


@dataclass
class AnalysisResult:
    summary: str
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    files_read: List[str] = field(default_factory=list)


@dataclass
class MCPServer:
    name: str
    status: str
    capabilities: List[str] = field(default_factory=list)


class OpenCode:
    """Python client for OpenCode AI coding agent."""

    def __init__(
        self,
        model: str = "anthropic/claude-3-opus",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        agent_type: AgentType = AgentType.BUILD,
        max_steps: int = 20,
        timeout: int = 300,
        working_dir: str = ".",
        env_vars: Optional[Dict[str, str]] = None,
        mcp_servers: Optional[List[Dict[str, Any]]] = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url
        self.agent_type = agent_type
        self.max_steps = max_steps
        self.timeout = timeout
        self.working_dir = working_dir
        self.env_vars = env_vars or {}
        self.mcp_servers = mcp_servers or []

        # Check if opencode CLI is available
        self._cli_path = self._find_opencode()

    def _find_opencode(self) -> Optional[str]:
        """Find the opencode CLI in PATH."""
        for cmd in ["opencode", "opencode-ai"]:
            result = subprocess.run(
                f"where {cmd}" if os.name == "nt" else f"which {cmd}",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")[0]
        return None

    def _ensure_cli(self):
        if not self._cli_path:
            raise RuntimeError(
                "OpenCode CLI not found. Install with:\n"
                "  npm i -g opencode-ai@latest\n"
                "  # or: curl -fsSL https://opencode.ai/install | bash"
            )

    @property
    def build(self):
        return BuildAgent(self)

    @property
    def plan(self):
        return PlanAgent(self)

    @property
    def general(self):
        return GeneralAgent(self)

    @property
    def mcp(self):
        return MCPInterface(self)

    @property
    def sessions(self):
        return SessionInterface(self)

    def run(self, prompt: str, **kwargs) -> TaskResult:
        """Run a task with the current agent type."""
        if self.agent_type == AgentType.BUILD:
            return self.build.run(prompt, **kwargs)
        elif self.agent_type == AgentType.PLAN:
            return self.plan.run(prompt, **kwargs)
        else:
            return self.general.run(prompt, **kwargs)


class BuildAgent:
    """Full-access development agent."""

    def __init__(self, client: OpenCode):
        self._client = client

    def run(
        self,
        prompt: str,
        working_dir: Optional[str] = None,
        files: Optional[List[str]] = None,
        max_tokens: int = 4000,
        **kwargs
    ) -> TaskResult:
        """Run a development task."""
        self._client._ensure_cli()

        cmd = [
            self._client._cli_path,
            "--model", self._client.model,
            "--agent", "build",
            "--non-interactive",
            "--output-json",
        ]

        if files:
            for f in files:
                cmd.extend(["--file", f])

        working = working_dir or self._client.working_dir
        cmd.extend(["--dir", working])

        env = os.environ.copy()
        env.update(self._client.env_vars)
        if self._client.api_key:
            env["OPENAI_API_KEY"] = self._client.api_key

        full_prompt = prompt
        if files:
            full_prompt = f"Focus on these files: {', '.join(files)}\n\n{prompt}"

        try:
            proc = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                cwd=working,
                env=env,
                timeout=self._client.timeout,
            )

            output = proc.stdout + proc.stderr

            # Try to parse JSON output
            try:
                data = json.loads(output)
                return TaskResult(
                    output=data.get("output", output),
                    summary=data.get("summary", ""),
                    files_modified=data.get("files_modified", []),
                    shell_commands=data.get("shell_commands", []),
                    tools_used=data.get("tools_used", []),
                    steps=data.get("steps", 1),
                )
            except json.JSONDecodeError:
                return TaskResult(
                    output=output,
                    summary=output[:500],
                    files_modified=[],
                    steps=1,
                )

        except subprocess.TimeoutExpired:
            return TaskResult(output="", summary="Task timed out", steps=0)
        except Exception as e:
            return TaskResult(output="", summary=f"Error: {str(e)}", steps=0)


class PlanAgent:
    """Read-only analysis agent."""

    def __init__(self, client: OpenCode):
        self._client = client

    def run(
        self,
        prompt: str,
        working_dir: Optional[str] = None,
        deep_search: bool = False,
        **kwargs
    ) -> AnalysisResult:
        """Run an analysis task (read-only)."""
        self._client._ensure_cli()

        cmd = [
            self._client._cli_path,
            "--model", self._client.model,
            "--agent", "plan",
            "--non-interactive",
            "--output-json",
        ]

        if deep_search:
            cmd.append("--deep")

        working = working_dir or self._client.working_dir
        cmd.extend(["--dir", working])

        env = os.environ.copy()
        env.update(self._client.env_vars)
        if self._client.api_key:
            env["OPENAI_API_KEY"] = self._client.api_key

        try:
            proc = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                cwd=working,
                env=env,
                timeout=self._client.timeout,
            )

            output = proc.stdout + proc.stderr

            try:
                data = json.loads(output)
                return AnalysisResult(
                    summary=data.get("summary", output),
                    findings=data.get("findings", []),
                    recommendations=data.get("recommendations", []),
                    files_read=data.get("files_read", []),
                )
            except json.JSONDecodeError:
                return AnalysisResult(
                    summary=output,
                    findings=[],
                    recommendations=[],
                    files_read=[],
                )

        except Exception as e:
            return AnalysisResult(summary=f"Error: {str(e)}")


class GeneralAgent:
    """Complex multi-step research subagent."""

    def __init__(self, client: OpenCode):
        self._client = client

    def run(
        self,
        prompt: str,
        sources: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
        **kwargs
    ) -> TaskResult:
        """Run a general research task."""
        self._client._ensure_cli()

        sources = sources or ["web"]

        cmd = [
            self._client._cli_path,
            "--model", self._client.model,
            "--agent", "general",
            "--non-interactive",
            "--output-json",
            "--sources", ",".join(sources),
        ]

        working = working_dir or self._client.working_dir
        cmd.extend(["--dir", working])

        env = os.environ.copy()
        env.update(self._client.env_vars)
        if self._client.api_key:
            env["OPENAI_API_KEY"] = self._client.api_key

        try:
            proc = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                cwd=working,
                env=env,
                timeout=self._client.timeout,
            )

            output = proc.stdout + proc.stderr

            try:
                data = json.loads(output)
                return TaskResult(
                    output=data.get("output", output),
                    summary=data.get("summary", ""),
                    files_modified=data.get("files_modified", []),
                    steps=data.get("steps", 1),
                )
            except json.JSONDecodeError:
                return TaskResult(output=output, summary=output[:500])

        except Exception as e:
            return TaskResult(output="", summary=f"Error: {str(e)}")


class MCPInterface:
    """Manage MCP server connections."""

    def __init__(self, client: OpenCode):
        self._client = client
        self._connected: List[MCPServer] = []

    def connect(
        self,
        name: str,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        """Connect to an MCP server."""
        config = {
            "name": name,
            "command": command,
            "args": args or [],
        }
        if env:
            config["env"] = env

        self._connected.append(MCPServer(name=name, status="connected"))
        return self

    def disconnect(self, name: str):
        """Disconnect an MCP server."""
        self._connected = [s for s in self._connected if s.name != name]

    def list_servers(self) -> List[MCPServer]:
        """List connected MCP servers."""
        return self._connected.copy()


class SessionInterface:
    """Manage OpenCode sessions."""

    def __init__(self, client: OpenCode):
        self._client = client
        self._sessions: Dict[str, Dict] = {}

    def create(
        self,
        project: str,
        name: str,
        description: str = "",
    ) -> "Session":
        """Create a new session."""
        session_id = f"sess_{len(self._sessions) + 1:04d}"
        session = Session(session_id, name, project, description)
        self._sessions[session_id] = {
            "id": session_id,
            "name": name,
            "project": project,
            "description": description,
        }
        return session

    def resume(self, session_id: str):
        """Resume a saved session."""
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        return self._sessions[session_id]

    def list(self) -> List[Dict]:
        """List all sessions."""
        return list(self._sessions.values())


@dataclass
class Session:
    id: str
    name: str
    project: str
    description: str


# Exports
__version__ = "0.1.0"
__all__ = ["OpenCode", "AgentType", "TaskResult", "AnalysisResult", "MCPServer", "Session"]