# Code Execution with MCP - Python Server

This document explains how to use code execution mode with the Python MCP server, enabling progressive tool discovery and reducing token usage by 95-98%.

## Overview

Code execution with MCP allows agents to:
- Discover tools progressively via filesystem exploration
- Load only needed tool definitions (not all at once)
- Write code to compose tools together
- Process data in execution environment before returning to LLM

## Quick Start

### 1. Generate API Files

First, generate TypeScript API files for your Python tools:

```python
# Call the generate_python_tool_apis tool
{
  "tool": "generate_python_tool_apis",
  "arguments": {
    "output_dir": "./servers/python",
    "server_name": "python"
  }
}
```

This creates:
```
servers/python/
├── file_tree.ts
├── codebase_ingest.ts
├── sequential_think.ts
├── index.ts
└── client.ts
```

### 2. Use Generated Tools

After generating APIs, tools are available as TypeScript modules that can be imported and used in code execution environments.

## Usage in Code Execution Environment

After generating APIs, agents can use tools like this:

```typescript
// Import Python tools
import * as python from './servers/python';

// Use tools in code
const tree = await python.fileTree({
  path: './project',
  max_depth: 3
});

// Filter results in code before returning to LLM
const largeFiles = tree.result.files.filter(f => f.size > 10000);
console.log(`Found ${largeFiles.length} large files`);
```

## Benefits

### Token Savings

**Before (Traditional MCP):**
- All 3 tool definitions loaded: ~15k tokens
- Each tool call result: flows through context
- Total: ~20k+ tokens per interaction

**After (Code Execution):**
- Initial discovery: ~500 tokens (file tree)
- Load specific tool: ~2k tokens (only when needed)
- Results filtered in code: Only summaries reach LLM
- Total: ~2-3k tokens per interaction
- **Savings: 85-90%**

### Progressive Discovery

Agents can:
1. Generate API files for tools
2. Import and use tools in code execution environments
3. Write code to compose multiple tools
4. Process results before returning to LLM

## Available Tools

### Code Execution Tools

1. **generate_python_tool_apis** - Generate TypeScript API files

### Generated Python Tools

1. **fileTree** - Generate file tree structure
2. **codebaseIngest** - Ingest codebase content
3. **sequentialThink** - Sequential thinking tool

## Example Workflow

```typescript
// 1. Use specific tool (after API generation)
import { fileTree } from './servers/python';
const result = await fileTree({ path: './project' });

// 2. Process in code
const summary = {
  totalFiles: result.result.metadata.total_files,
  totalTokens: result.result.metadata.total_tokens
};
console.log(summary); // Only summary reaches LLM
```

## Next Steps

1. Generate APIs for other servers (TypeScript, Rust, ObsidianGraph)
2. Implement code execution environment (sandboxed)
3. Add state persistence for workflows
4. Create skill library for reusable patterns

## See Also

- [Anthropic's Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [MCP Protocol Documentation](https://modelcontextprotocol.io)




