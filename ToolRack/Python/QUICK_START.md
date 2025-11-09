# AiChemistForge Python MCP Server - Quick Start Guide

## 🚀 Installation & Setup

### 1. Install Dependencies
```powershell
cd ToolRack/Python
uv sync --all-groups
```

### 2. Configure Environment (Optional)
```powershell
# Copy example and customize
cp .env.example .env
# Edit .env with your settings
```

### 3. Start Server
```powershell
# STDIO mode (default - for MCP clients)
.\start_mcp_server.bat

# HTTP mode (for testing/debugging)
.\start_mcp_server_http.bat
```

### 4. Verify Installation
```powershell
# Quick test
python test_mcp_server.py

# Detailed verification
uv run python -c "from unified_mcp_server.main import mcp; print('✅ Server ready:', mcp.name)"
```

---

## 🔧 Configuration

### Key Environment Variables

```bash
# Logging
MCP_LOG_LEVEL="INFO"              # DEBUG, INFO, WARNING, ERROR

# Performance
OPERATION_TIMEOUT="300"            # Seconds
RETRY_MAX_ATTEMPTS="3"             # Retry count
MAX_FILE_SIZE="20000000"           # 20MB

# Monitoring
METRICS_ENABLED="true"             # Enable metrics collection
TRACING_ENABLED="true"             # Enable request tracing
HEALTH_CHECKS_ENABLED="true"       # Enable health checks

# Rate Limiting (optional)
RATE_LIMIT_ENABLED="false"         # Enable rate limiting
RATE_LIMIT_REQUESTS="100"          # Requests per window
RATE_LIMIT_WINDOW="60"             # Window in seconds
```

---

## 🛠️ Available Tools

| Tool | Purpose | Use Case |
|------|---------|----------|
| `file_tree` | Generate file tree with analysis | Project structure overview |
| `codebase_ingest` | Ingest full codebase | Complete code analysis |
| `sequential_think` | Step-by-step reasoning | Complex problem solving |
| `decompose_problem` | Break down problems | Task planning |
| `analyze_dependencies` | Analyze dependencies | Architectural analysis |
| `decompose_and_think` | Combined analysis | Deep problem exploration |

---

## 📊 Monitoring

### Check Server Health
```python
from unified_mcp_server.server.lifecycle import get_lifecycle_manager
lifecycle = get_lifecycle_manager()
print(lifecycle.is_healthy())
```

### View Metrics
```python
from unified_mcp_server.server.metrics import get_metrics_collector
metrics = get_metrics_collector()
print(metrics.get_summary())
```

### View Tool Stats
```python
from unified_mcp_server.server.metrics import get_metrics_collector
metrics = get_metrics_collector()
for tool_name, tool_metrics in metrics._tools.items():
    print(f"{tool_name}: {tool_metrics.total_calls} calls, {tool_metrics.avg_latency:.2f}ms avg")
```

---

## 🐛 Troubleshooting

### Server Won't Start
```powershell
# Check dependencies
uv sync --all-groups

# Verify Python path
$env:PYTHONPATH="src"

# Check imports
uv run python -c "import unified_mcp_server; print('OK')"
```

### Tools Not Found
```powershell
# List registered tools
uv run python -c "from unified_mcp_server.main import mcp; print(list(mcp._tool_manager._tools.keys()))"
```

### Performance Issues
```powershell
# Enable debug logging
$env:MCP_LOG_LEVEL="DEBUG"
.\start_mcp_server.bat

# Check system resources
# (metrics will show CPU/memory usage)
```

### Connection Issues
```powershell
# For STDIO: Check client stderr for errors
# For HTTP: Test endpoint
curl http://localhost:9876/health
```

---

## 📚 Documentation

- **Architecture**: `docs/SERVER_ARCHITECTURE.md`
- **Performance**: `docs/PERFORMANCE_TUNING.md`
- **Monitoring**: `docs/MONITORING.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **Complete Summary**: `IMPLEMENTATION_COMPLETE.md`

---

## 🎯 Common Workflows

### 1. Analyze a Codebase
```python
# 1. Get project structure
file_tree(path="D:\\MyProject", max_depth=5)

# 2. Ingest important files
codebase_ingest(
    root_directory="D:\\MyProject",
    include_patterns=["*.py"],
    max_file_size=100000
)

# 3. Analyze with reasoning
sequential_think(
    problem="How is authentication implemented?",
    max_steps=10
)
```

### 2. Debug Performance
```bash
# Enable metrics
export METRICS_ENABLED=true
export TRACING_ENABLED=true

# Start server
.\start_mcp_server.bat

# Use tools...

# Check metrics
python -c "from unified_mcp_server.server.metrics import get_metrics_collector; print(get_metrics_collector().get_summary())"
```

### 3. Custom Configuration
```bash
# Create environment file
cat > .env << EOF
MCP_LOG_LEVEL=DEBUG
OPERATION_TIMEOUT=600
METRICS_ENABLED=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=50
EOF

# Start with config
.\start_mcp_server.bat
```

---

## 🔒 Security

### Best Practices
- ✅ Never commit `.env` files (already in `.gitignore`)
- ✅ Use environment variables for secrets
- ✅ Enable rate limiting in production
- ✅ Monitor metrics for unusual activity
- ✅ Keep dependencies updated (`uv sync --upgrade`)

### Safe Paths
- File tools validate paths to prevent traversal attacks
- Use absolute paths when possible
- Check `MAX_FILE_SIZE` limits

---

## 🚦 Production Deployment

### 1. Use Production Environment
```bash
# Use .env.production
cp .env.production .env

# Or set directly
export MCP_LOG_LEVEL=WARNING
export METRICS_ENABLED=true
export HEALTH_CHECKS_ENABLED=true
```

### 2. Configure MCP Client
```json
{
  "mcpServers": {
    "aichemist-forge": {
      "command": "uv",
      "args": ["run", "unified-mcp-server"],
      "cwd": "/path/to/ToolRack/Python",
      "env": {
        "MCP_LOG_LEVEL": "WARNING",
        "METRICS_ENABLED": "true"
      }
    }
  }
}
```

### 3. Monitor Health
```python
# Regular health checks
from unified_mcp_server.server.lifecycle import get_lifecycle_manager
assert get_lifecycle_manager().is_healthy()

# Track metrics
from unified_mcp_server.server.metrics import get_metrics_collector
metrics = get_metrics_collector()
summary = metrics.get_summary()
# Alert if error_rate > threshold
```

---

## 📞 Support

### Logs
- **STDIO Mode**: Check MCP client stderr
- **HTTP Mode**: Check console output
- **Debug Mode**: Set `MCP_LOG_LEVEL=DEBUG`

### Issues
- Check `TROUBLESHOOTING.md` for common issues
- Verify dependencies with `uv sync --all-groups`
- Test with `python test_mcp_server.py`

---

## ✅ Quick Health Check

```powershell
# One-command verification
cd ToolRack/Python && uv run python -c "
from unified_mcp_server.main import mcp
from unified_mcp_server.server.lifecycle import get_lifecycle_manager
print('Server:', mcp.name)
print('Tools:', len(list(mcp._tool_manager._tools.keys())))
print('Healthy:', get_lifecycle_manager().is_healthy())
print('✅ All systems operational!')
"
```

---

**Server Version**: 2.0
**Last Updated**: November 8, 2025
**Status**: Production Ready 🚀












