# TypeScript MCP Server - File Structure Explanation

## Why You Have 2 Server Files

You currently have **three server-related files** in your TypeScript project:

### 1. **`src/index.ts`** (Entry Point)
```typescript
import './server/server.js';
```
- **Purpose**: Main entry point defined in `package.json`
- **Status**: ✅ Active (imports the correct server)
- **Used by**: `npm start` → `node dist/index.js`

### 2. **`src/server/server.ts`** (NEW/CORRECT Implementation)
- **Purpose**: Modern MCP server implementation
- **SDK Used**: `McpServer` from `@modelcontextprotocol/sdk/server/mcp.js`
- **Features**:
  - ✅ Cleaner `registerTool()` API
  - ✅ Better error handling with `wrapToolExecution()`
  - ✅ Proper logger from utils
  - ✅ More maintainable structure
- **Status**: ✅ **This is the CORRECT one to use**
- **Used by**: `src/index.ts` imports this

### 3. **`src/server.ts`** (OLD/LEGACY Implementation)
- **Purpose**: Older MCP server implementation
- **SDK Used**: `Server` from `@modelcontextprotocol/sdk/server/index.js`
- **Features**:
  - ⚠️ Manual `setRequestHandler()` for each operation
  - ⚠️ Switch statement for tool routing
  - ⚠️ Requires `zodToJsonSchema` conversion
  - ⚠️ Less structured error handling
- **Status**: ⚠️ **LEGACY - Should be removed**
- **Used by**: Nothing currently (orphaned file)

## What Happened?

This situation occurred because:

1. **Originally**: You had `src/server.ts` using the older MCP SDK pattern
2. **Later**: Created `src/server/server.ts` with the newer `McpServer` API
3. **Updated**: `src/index.ts` to import the new server
4. **Forgot**: To delete the old `src/server.ts` file

## Current Startup Flow

### NPM Start (Correct)
```
npm start
  ↓
node dist/index.js
  ↓
imports dist/server/server.js
  ↓
✅ NEW server runs
```

### Batch File (Was Incorrect - Now Fixed)
```
start_mcp_server.bat
  ↓
node dist/server/server.js  ← Fixed to use correct path
  ↓
✅ NEW server runs directly
```

## Changes Made

### ✅ Fixed `start_mcp_server.bat`
**Before:**
```batch
if not exist "dist\server.js" (
node dist\server.js
```

**After:**
```batch
if not exist "dist\server\server.js" (
node dist\server\server.js
```

### ✅ Updated Multi-Link Search Description
Updated the tool description in `src/server/server.ts` to reflect sequential execution:
- Changed from "concurrent" to "sequential"
- Added note about 1.1s per query processing time
- Added rate limit context

## Recommended Next Steps

### 1. **Delete the Old Server (Recommended)**
```bash
cd ToolRack/TypeScript
rm src/server.ts
```

This file is orphaned and no longer used. Keeping it causes confusion.

### 2. **Rebuild the Project**
```bash
npm run build
```

### 3. **Test Both Startup Methods**
```bash
# Method 1: NPM script
npm start

# Method 2: Batch file
start_mcp_server.bat
```

Both should now use the same modern server implementation.

## File Structure After Cleanup

```
ToolRack/TypeScript/
├── src/
│   ├── index.ts                    ✅ Entry point
│   ├── server/
│   │   └── server.ts              ✅ Modern MCP server (KEEP)
│   ├── tools/
│   │   ├── braveSearchTools.ts    ✅ With retry logic
│   │   └── winCliTools.ts         ✅ CLI tools
│   └── utils/
│       └── logger.ts              ✅ Logger utility
├── dist/                           (compiled output)
├── package.json                    ✅ Points to dist/index.js
└── start_mcp_server.bat           ✅ Now points to dist/server/server.js
```

## Key Differences Between Old and New Server

### Old Server (`src/server.ts` - REMOVE)
```typescript
// Manual handler registration
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: [...] };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  switch (name) {
    case 'brave_web_search':
      return await executeWebSearch(args);
    // ... more cases
  }
});
```

### New Server (`src/server/server.ts` - KEEP)
```typescript
// Clean tool registration
server.registerTool(
  "brave_web_search",
  {
    description: "...",
    inputSchema: { ... },
    annotations: { title: "..." }
  },
  async (args) => wrapToolExecution("brave_web_search", executeWebSearch, args)
);
```

## Benefits of New Server

1. **Less Boilerplate**: No need to manually handle ListTools and CallTool requests
2. **Type Safety**: Better TypeScript integration with `registerTool()`
3. **Error Handling**: Centralized error handling via `wrapToolExecution()`
4. **Logging**: Consistent logging for all tool executions
5. **Maintainability**: Adding new tools is simpler
6. **Modern SDK**: Uses latest MCP SDK patterns

## Verification

To verify everything is working:

```bash
cd ToolRack/TypeScript

# 1. Clean build
npm run build

# 2. Check compiled files exist
ls dist/index.js        # Should exist
ls dist/server/server.js # Should exist

# 3. Test startup
npm start
# Should see: "AiChemistForge MCP Server connected and listening on stdio."

# 4. Test batch file
start_mcp_server.bat
# Should see: "TypeScript MCP Server connected and listening on stdio."
```

## Summary

- ✅ **Keep**: `src/index.ts` (entry point)
- ✅ **Keep**: `src/server/server.ts` (modern implementation)
- ❌ **Remove**: `src/server.ts` (legacy orphaned file)
- ✅ **Fixed**: `start_mcp_server.bat` now uses correct path
- ✅ **Updated**: Tool descriptions to reflect sequential execution

The confusion came from having both old and new implementations. Now that we've fixed the batch file and identified the orphaned file, you can safely delete `src/server.ts` and continue using the modern `src/server/server.ts` implementation.


