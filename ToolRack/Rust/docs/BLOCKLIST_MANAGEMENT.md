# Managing Blocked Directories

## ✅ You Already Have This!

Your MCP server is configured for **zero-config** operation:
- No args needed in MCP config
- All directories allowed EXCEPT blocked ones
- Blocklist managed in `forbidden_dirs.txt`

## 📝 How to Block/Unblock Directories

### Add a Blocked Directory
1. Open `forbidden_dirs.txt`
2. Add the path (one per line):
   ```
   D:\SensitiveFolder
   C:\PrivateData
   ```
3. Restart the MCP server (restart Cursor)

### Remove a Blocked Directory
1. Open `forbidden_dirs.txt`
2. Delete the line or comment it out with `#`:
   ```
   # C:\Users\Public  ← Now allowed again
   ```
3. Restart the MCP server

### View Current Blocked Directories
When the server starts, it logs the blocklist to stderr:
```
Default blocked directories: C:\Windows,C:\Program Files,...
```

## 🎯 Your Current MCP Config (Perfect!)

```json
{
  "mcpServers": {
    "Rust": {
      "command": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Rust\\start_mcp_server.bat",
      "args": [],  // ← Empty! Batch file handles everything
      "type": "stdio"
    }
  }
}
```

## 🔒 Default Blocked Directories

These are blocked automatically for security:
- `C:\Windows` - System files
- `C:\Windows\System32` - Critical system DLLs
- `C:\Program Files` - Installed programs
- `C:\Program Files (x86)` - 32-bit programs
- `C:\ProgramData` - Application data
- `C:\System Volume Information` - System restore
- `C:\$Recycle.Bin` - Deleted files
- `C:\Recovery` - Recovery partition

## ✨ Everything Else is Allowed

The server can access:
- ✅ `D:\` drive (all folders)
- ✅ `E:\`, `F:\`, etc. (all other drives)
- ✅ `C:\Users\YourName\` (your user folder)
- ✅ Any folder not in `forbidden_dirs.txt`

## 🚀 Workflow Examples

### Scenario 1: Block a project folder temporarily
```bash
# Add to forbidden_dirs.txt
D:\Coding\SensitiveProject

# Restart Cursor
# Now D:\Coding\SensitiveProject is blocked
```

### Scenario 2: Allow more system folders
```bash
# Comment out in forbidden_dirs.txt
# C:\ProgramData  ← Now accessible

# Restart Cursor
```

### Scenario 3: Block by pattern (NOT SUPPORTED YET)
Currently, you must list exact paths. Wildcards are not supported:
```bash
# This WON'T work:
# C:\Users\*\AppData

# Instead, list specific paths:
C:\Users\Steve\AppData
C:\Users\Admin\AppData
```

## 🔧 Advanced: Dynamic Blocklist via MCP Config

If you need to override the blocklist for a specific MCP client, you CAN add args:

```json
{
  "mcpServers": {
    "Rust": {
      "command": "D:\\...\\start_mcp_server.bat",
      "args": ["--blocked-directories", "D:\\Extra,C:\\MoreBlocked"],
      "type": "stdio"
    }
  }
}
```

This **ADDS** to the default blocklist from `forbidden_dirs.txt`.

## 📊 Access Control Summary

| Configuration | Result |
|---------------|--------|
| No args + `forbidden_dirs.txt` | ✅ Current setup (recommended) |
| No args + empty `forbidden_dirs.txt` | ⚠️ Unrestricted (everything allowed) |
| Args with `--blocked-directories` | Adds to `forbidden_dirs.txt` blocklist |
| Args with positional paths | **RESTRICTED** mode (only those paths allowed) |

## 🎉 TL;DR

**You're done!** Your setup is perfect:
1. ✅ No args needed in MCP config
2. ✅ Edit `forbidden_dirs.txt` to manage blocklist
3. ✅ Everything else is accessible
4. ✅ Just restart Cursor when you change the blocklist

---

**File Locations:**
- MCP Config: `D:\Coding\AiChemistCodex\AiChemistForge\.cursor\mcp.json`
- Blocklist: `D:\Coding\AiChemistCodex\AiChemistForge\ToolRack\Rust\forbidden_dirs.txt`

