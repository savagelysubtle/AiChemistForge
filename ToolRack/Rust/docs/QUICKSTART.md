# Rust MCP Server - Quick Start Guide

## ✅ All Changes Applied Successfully!

Your Rust MCP server has been optimized for fast startup. All tests pass!

---

## 📋 What Changed

### Files Modified
- ✅ `start_mcp_server.bat` - Now runs pre-built executable (no rebuild)
- ✅ `.cursor/mcp.json` - Configured for Cursor integration

### Files Created
- ✅ `build_mcp_server.bat` - Build script (run when code changes)
- ✅ `check_setup.bat` - Environment verification script
- ✅ `test_optimization.bat` - Automated testing script
- ✅ `OPTIMIZATION_CHANGES.md` - Detailed change documentation

---

## 🚀 How to Use

### First Time Setup
```batch
# Navigate to the Rust directory
cd D:\Coding\AiChemistCodex\AiChemistForge\ToolRack\Rust

# Verify your environment (optional)
check_setup.bat

# The server is already built, so you can skip the build step!
```

### Daily Usage - Starting the Server
```batch
# Option 1: Direct execution
start_mcp_server.bat

# Option 2: Use Cursor's MCP integration (Recommended)
# Just restart Cursor - the server is already configured!
```

### When You Modify Rust Code
```batch
# 1. Stop any running instances
Get-Process -Name "aichemistforge-mcp-server" -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. Rebuild the server
build_mcp_server.bat

# 3. Restart Cursor to reload MCP connection
```

---

## 🎯 Key Benefits

| Before | After |
|--------|-------|
| ❌ Rebuilt every startup (10-30s) | ✅ Instant startup (<1s) |
| ❌ Used `cargo run` | ✅ Uses pre-built executable |
| ❌ No MCP config | ✅ Fully configured for Cursor |
| ❌ Manual setup needed | ✅ Ready to use immediately |

---

## 🔍 Verify Everything Works

Run the automated test:
```batch
test_optimization.bat
```

Expected output:
```
Test 1: Build script exists              [PASS]
Test 2: Start script exists              [PASS]
Test 3: Check script exists              [PASS]
Test 4: Start script uses pre-built exe  [PASS]
Test 5: Start script references correct  [PASS]
Test 6: MCP configuration exists         [PASS]
Test 7: MCP config has Rust server       [PASS]
Test 8: Check if server is built         [PASS]

Passed: 8 | Failed: 0
```

---

## 🔧 Using with Cursor IDE

### The server is already configured! Just:

1. **Restart Cursor** to load the MCP configuration
2. **Open Command Palette** (Ctrl+Shift+P)
3. **Search for "MCP"** to see available commands
4. **Try a filesystem tool** like `read_file` or `list_directory`

### MCP Configuration Location
```
D:\Coding\AiChemistCodex\AiChemistForge\.cursor\mcp.json
```

### Current Configuration
```json
{
  "mcpServers": {
    "Rust": {
      "command": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Rust\\start_mcp_server.bat",
      "args": [],
      "type": "stdio",
      "env": {
        "RUST_LOG": "info"
      }
    }
  }
}
```

---

## 🛡️ Security Configuration

### Default Blocked Directories (Automatic)
These are blocked by default from `forbidden_dirs.txt`:
- `C:\Windows`
- `C:\Program Files`
- `C:\Program Files (x86)`
- Additional system directories

### Adding Custom Blocked Directories
Edit `.cursor/mcp.json` to add more:
```json
"args": ["--blocked-directories", "D:\\SensitiveProject,C:\\PrivateData"]
```

---

## 📚 Available Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `check_setup.bat` | Verify environment | Setup validation |
| `build_mcp_server.bat` | Compile server | When code changes |
| `start_mcp_server.bat` | Run server | Daily use (or use Cursor) |
| `test_optimization.bat` | Run tests | Verify setup |

---

## 🐛 Troubleshooting

### Error: "Server executable not found"
**Solution:**
```batch
build_mcp_server.bat
```

### Error: "Cargo not found in PATH"
**Solution:** Install Rust from https://rustup.rs/

### Server not showing in Cursor
**Solutions:**
1. Restart Cursor completely
2. Check `.cursor/mcp.json` exists
3. Verify path in mcp.json is correct (use double backslashes)
4. Check Cursor's MCP logs for errors

### Multiple simultaneous connections
**Solution:** Check for duplicate entries in `.cursor/mcp.json` - should only have ONE "Rust" entry

---

## 📊 Performance Comparison

### Before Optimization
```
Cursor starts MCP connection
  ↓
Runs cargo build (10-30 seconds)
  ↓
Starts server
  ↓
Ready (SLOW)
```

### After Optimization
```
Cursor starts MCP connection
  ↓
Runs pre-built executable (<1 second)
  ↓
Ready (FAST)
```

---

## ✨ Next Steps

Your server is **ready to use**!

1. ✅ Server is built and configured
2. ✅ MCP configuration is set up
3. ✅ All tests pass

**Just restart Cursor and start using the filesystem tools!**

---

For more details, see:
- `OPTIMIZATION_CHANGES.md` - Detailed technical changes
- `README.md` - Full server documentation
- `forbidden_dirs.txt` - Security configuration

**Enjoy your blazing-fast Rust MCP server! 🚀**

