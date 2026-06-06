# OpenCode Wrapper🤖

> The open source AI coding agent — now available as a Python/TypeScript library wrapper.

## What is OpenCode?

**OpenCode** is an open-source AI coding agent that helps developers write, review, and refactor code. It supports both terminal and desktop interfaces, and can be integrated into existing tools and workflows via this wrapper.

This wrapper provides a programmatic Python/TypeScript interface for launching OpenCode sessions, managing agents, and integrating OpenCode into custom toolchains.

##⭐ Key Features

- **Build Agent** — Full-access autonomous agent for development work
- **Plan Agent** — Read-only analysis and code exploration
- **General Subagent** — Complex multi-step searches and tasks
- **MCP Integration** — Connect to Model Context Protocol servers
- **Desktop App** — Cross-platform GUI application
- **Terminal CLI** — Install and run via curl/npm/brew
- **Multi-language** — Available in 20+ languages

## 📦 Installation

### Python

```bash
pip install opencode-wrap
```

### Node.js / TypeScript

```bash
npm install opencode-wrap
# or
yarn add opencode-wrap
# or
pnpm add opencode-wrap
```

## 🚀 Quick Start

### Python

```python
from opencode import OpenCode

# Initialize the client
client = OpenCode(
    model="anthropic/claude-3-opus",  # or openai/gpt-4o, etc.
    api_key="your-api-key"
)

# Run a build task
result = client.build.run(
    prompt="Create a REST API for a todo list with FastAPI",
    working_dir="/path/to/project"
)
print(result.output)
print(result.files_modified)

# Run a plan/analysis task
analysis = client.plan.run(
    prompt="Analyze the codebase and identify performance bottlenecks",
    working_dir="/path/to/project"
)
print(analysis.summary)
```

### TypeScript / JavaScript

```typescript
import { OpenCode } from 'opencode-wrap';

const client = new OpenCode({
  model: 'anthropic/claude-3-opus',
  apiKey: process.env.OPENCODE_API_KEY
});

// Run a build task
const result = await client.build.run({
  prompt: 'Add user authentication to this Express app',
  workingDir: './my-app'
});

console.log(result.output);
console.log(result.filesModified);
```

## 🔧 Configuration

```python
from opencode import OpenCode, AgentType

client = OpenCode(
    # Model configuration
    model="anthropic/claude-3-opus",
    api_key="sk-...", # API key for model provider
    base_url=None,                 # Custom endpoint (for proxies/self-hosted)

    # Agent defaults
    agent_type=AgentType.BUILD,    # BUILD / PLAN / GENERAL
    max_steps=20,
    timeout=300,

    # Working environment
    working_dir="./workspace",
    env_vars={}, # Extra environment variables

    # MCP servers
    mcp_servers=[
        {"name": "filesystem", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]}
    ]
)
```

## 📚 API Reference

### Agents

OpenCode includes three built-in agent types:

| Agent | Description | File Edits | Shell Commands |
|-------|-------------|-----------|----------------|
| `BUILD` | Full-access development | ✅ | ✅ |
| `PLAN` | Read-only analysis | ❌ | Ask first |
| `GENERAL` | Complex multi-step tasks | Via BUILD | ✅ |

```python
# Switch between agents with Tab key behavior
client.agent_type = AgentType.PLAN
analysis = client.plan.run("Summarize this codebase architecture")

client.agent_type = AgentType.BUILD
task = client.build.run("Fix all TODO comments in the codebase")
```

### Build Agent

```python
# Full development task
result = client.build.run(
    prompt="Refactor the authentication module to use JWT",
    working_dir="/project",
    files=["auth.py", "middleware.py"],  # Focus on specific files
    max_tokens=4000
)

print(f"Modified {len(result.files_modified)} files:")
for f in result.files_modified:
    print(f" 📝 {f.path}")

print(f"\n📋 Summary:\n{result.summary}")
```

### Plan Agent

```python
# Code exploration without making changes
analysis = client.plan.run(
    prompt="""
    Explore the database layer of this codebase.
    Identify:
    1. All database models and their relationships
    2. Query patterns that might cause N+1 problems
    3. Missing indexes
    """,
    working_dir="/project",
    deep_search=True  # Enable comprehensive codebase scan
)

print(analysis.findings)
print(analysis.recommendations)
```

### General Subagent

```python
# Complex multi-step research tasks
research = client.general.run(
    prompt="""
    Research best practices for:
    1. PostgreSQL connection pooling
    2. Redis caching strategies
    3. Rate limiting approaches

    Summarize each with pros/cons and implementation notes.
    """,
    sources=["web", "docs", "github"]
)
```

### MCP Server Integration

```python
# Connect to MCP servers for extended capabilities
client.mcp.connect(
    name="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/project"]
)

client.mcp.connect(
    name="brave-search",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-brave-search"],
    env={"BRAVE_API_KEY": "your-key"}
)

# List connected servers
servers = client.mcp.list_servers()
for s in servers:
    print(f"  • {s.name} ({s.status})")
```

### Session Management

```python
# Save and resume sessions
session = client.sessions.create(
    project="/project",
    name="refactor-auth-session",
    description="JWT authentication refactoring"
)

# Do work...
result = client.build.run(prompt="Refactor auth to JWT")

# Resume later
client.sessions.resume(session.id)
```

## 🖥️ Desktop App

OpenCode also ships as a cross-platform desktop application:

| Platform | Download |
|----------|----------|
| macOS (Apple Silicon) | `opencode-desktop-mac-arm64.dmg` |
| macOS (Intel) | `opencode-desktop-mac-x64.dmg` |
| Windows | `opencode-desktop-windows-x64.exe` |
| Linux | `.deb`, `.rpm`, `.AppImage` |

```bash
# macOS Homebrew
brew install --cask opencode-desktop

# Windows Scoop
scoop bucket add extras
scoop install extras/opencode-desktop
```

## 🔒 Security

- The **Plan** agent denies file edits by default
- The **Plan** agent asks permission before running shell commands
- API keys are stored in environment variables, never in config files
- MCP server access is scoped to specified directories

## 📄 License

- **This wrapper**: MIT License
- **OpenCode**: MIT License — [anomalyco/opencode](https://github.com/anomalyco/opencode)

## 🔗 Links

- 🌐 [OpenCode Official](https://opencode.ai)
- 📖 [Documentation](https://opencode.ai/docs)
- 💬 [Discord](https://discord.gg/opencode)
- 🐛 [Report Issues](https://github.com/anomalyco/opencode/issues)
- 🐙 [GitHub](https://github.com/anomalyco/opencode)