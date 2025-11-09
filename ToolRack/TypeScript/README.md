# AiChemistForge - TypeScript MCP Server

A comprehensive Model Context Protocol (MCP) server built with TypeScript and
Node.js, providing web search, deep research, and Windows CLI execution
capabilities. This server is part of the larger AiChemistForge project but can
be run and developed as a standalone component.

## Features

- **🔍 Brave Search Integration**: Web and code-specific searches using the
  Brave Search API
- **🧠 Perplexity Deep Research**: Comprehensive deep research using Perplexity
  AI's sonar-deep-research model
- **💻 Windows CLI Tools**: Safe command execution with PowerShell, CMD, and Git
  Bash support
- **⚡ Semantic Caching**: Optional semantic similarity caching for faster
  repeated searches
- **🔄 Rate Limiting**: Built-in rate limiting and retry logic for API calls
- **📊 Result Processing**: Deduplication, domain limiting, and result
  formatting
- **🔒 Security**: Command validation, path restrictions, and destructive
  command protection
- **📝 Structured Logging**: Logger utility that outputs to `stderr` to keep
  `stdout` clean for JSON-RPC
- **🎯 Type Safety**: Full TypeScript with Zod schema validation

## Available Tools

### Brave Search Tools

#### `brave_web_search`

Performs general web searches using the Brave Search API.

- **Use Cases**: General information gathering, news, articles, recent events
- **Features**: Pagination support, content filtering, freshness controls
- **Limits**: Maximum 20 results per request, offset for pagination (0-9)
- **Input Parameters**:
  - `query` (string, required): Search query (max 400 chars, 50 words)
  - `count` (number, optional): Number of results (1-20, default 10)
  - `offset` (number, optional): Pagination offset (max 9, default 0)

#### `brave_code_search`

Searches developer-focused sites (Stack Overflow, GitHub, MDN, etc.) using Brave
Search.

- **Use Cases**: Code snippets, technical documentation, programming solutions
- **Features**: Targeted site search for relevance
- **Limits**: Maximum 20 results per request
- **Input Parameters**:
  - `query` (string, required): Code search query
  - `count` (number, optional): Number of results (1-20, default 10)

#### `multi_link_search`

Performs sequential web searches for multiple queries using the Brave Search
API.

- **Use Cases**: Batch information gathering across diverse topics
- **Features**: Sequential execution with delays to respect rate limits,
  aggregated results
- **Limits**: Up to 10 queries, ~1.1 seconds per query processing time
- **Input Parameters**:
  - `queries` (array, required): Array of search queries (1-10 items, each max
    400 chars)
  - `count` (number, optional): Number of results per query (1-20, default 10)

### Perplexity Deep Research

#### `perplexity_deep_research`

Performs comprehensive deep research using Perplexity AI's sonar-deep-research
model.

- **Use Cases**: In-depth research, market analysis, technical investigations,
  academic synthesis
- **Features**: Exhaustive searches across hundreds of sources, expert-level
  insights, detailed reports with citations
- **Processing Time**: 30-90 seconds per query
- **Input Parameters**:
  - `query` (string, required): Research query (10-2000 characters)
  - `search_recency_filter` (enum, optional): Filter sources by recency
    (`month`, `week`, `day`, `hour`)
  - `return_images` (boolean, optional): Include relevant images (default:
    false)
  - `return_related_questions` (boolean, optional): Include related research
    questions (default: false)

### Windows CLI Tools

#### `execute_command`

Execute Windows command line commands safely with validation and security
controls.

- **Shells Supported**: PowerShell, CMD, Git Bash
- **Security Features**: Command validation, path restrictions, destructive
  command protection
- **Input Parameters**:
  - `shell` (enum, required): Shell to use (`powershell`, `cmd`, `gitbash`)
  - `command` (string, required): Command to execute
  - `workingDir` (string, optional): Working directory for command execution
  - `dryRun` (boolean, optional): Preview command without executing
  - `force` (boolean, optional): Force execution of destructive commands

#### `get_command_history`

Retrieve recent command execution history.

- **Input Parameters**:
  - `limit` (number, optional): Maximum number of history entries to return

#### `get_current_directory`

Get comprehensive information about the current working directory, workspace
detection, and directory stack.

- **Input Parameters**: None

#### `change_directory`

Intelligently change the working directory with workspace detection and path
validation.

- **Input Parameters**:
  - `path` (string, required): Target directory path
  - `relative` (boolean, optional): Whether the path is relative to current
    directory

#### `find_workspace`

Find and analyze workspace information starting from a given directory,
detecting project types and configuration files.

- **Input Parameters**:
  - `startPath` (string, optional): Starting path to search (defaults to current
    directory)

## Prerequisites

- **Node.js**: Node.js 18+ (includes npm)
- **Brave Search API Key**: Required for Brave Search tools (get from
  [Brave Search API](https://brave.com/search/api/))
- **Perplexity API Key**: Required for Deep Research tool (get from
  [Perplexity AI](https://www.perplexity.ai/))
- **TypeScript**: Installed via npm (included in dev dependencies)

## Installation & Setup

1. **Navigate to the Server Directory:**

   ```bash
   cd AiChemistForge/ToolRack/TypeScript
   ```

2. **Install Dependencies:**

   ```bash
   npm install
   ```

3. **Set up Environment Variables:** Create a `.env` file in the
   `ToolRack/TypeScript/` directory:

   ```env
   # Required API Keys
   BRAVE_API_KEY=your_brave_api_key_here
   PERPLEXITY_API_KEY=your_perplexity_api_key_here

   # Optional: Logging
   LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARN, ERROR

   # Optional: Semantic Caching
   ENABLE_SEMANTIC_CACHE=false  # Set to 'true' to enable semantic caching
   ENABLE_DEDUPLICATION=true    # Enable result deduplication (default: true)
   CACHE_TTL_SECONDS=3600       # Cache time-to-live in seconds (default: 3600)
   MAX_RESULTS_PER_DOMAIN=2     # Maximum results per domain (default: 2)

   # Optional: Server Configuration
   MCP_SERVER_NAME=TypeScript
   NODE_ENV=production
   ```

4. **Build the TypeScript Code:**
   ```bash
   npm run build
   ```
   This compiles TypeScript to JavaScript in the `dist/` directory.

## Usage

### Running the Server

#### Windows (Batch Script - Recommended)

```batch
start_mcp_server.bat
```

The batch script:

- Checks for compiled JavaScript
- Verifies dependencies are installed
- Sets up environment variables
- Starts the server with proper stdio handling

#### Cross-Platform (Manual)

```bash
# Production mode
npm start

# Or directly with Node.js
node dist/server/server.js
```

#### Development Mode

```bash
# Watch mode (auto-rebuild and restart)
npm run dev
```

**Note**: The server uses stdio transport by default. All logs appear on
`stderr`, while JSON-RPC communication uses `stdout`.

### Connecting from an MCP Client (e.g., Cursor)

1. **Build the server first:**

   ```bash
   npm run build
   ```

2. **Configure MCP Client:** Add to Cursor's MCP settings (`.cursor/mcp.json` or
   global settings):

   ```json
   {
     "mcpServers": {
       "aichemistforge-typescript": {
         "command": "D:\\path\\to\\AiChemistForge\\ToolRack\\TypeScript\\start_mcp_server.bat",
         "cwd": "D:\\path\\to\\AiChemistForge\\ToolRack\\TypeScript",
         "env": {
           "LOG_LEVEL": "INFO"
         }
       }
     }
   }
   ```

   **Or use Node.js directly:**

   ```json
   {
     "mcpServers": {
       "aichemistforge-typescript": {
         "command": "node",
         "args": ["dist/server/server.js"],
         "cwd": "D:\\path\\to\\AiChemistForge\\ToolRack\\TypeScript",
         "env": {
           "BRAVE_API_KEY": "your_key_here",
           "PERPLEXITY_API_KEY": "your_key_here"
         }
       }
     }
   }
   ```

3. **Restart Cursor** to load the MCP server configuration

4. **Verify Connection:**
   - Open Cursor's command palette (Ctrl+Shift+P)
   - Search for "MCP" commands
   - You should see the TypeScript server listed with all available tools

## Configuration

### Environment Variables

#### Required

- **`BRAVE_API_KEY`**: Brave Search API key (required for Brave Search tools)
- **`PERPLEXITY_API_KEY`**: Perplexity AI API key (required for Deep Research
  tool)

#### Optional

- **`LOG_LEVEL`**: Logging verbosity (`DEBUG`, `INFO`, `WARN`, `ERROR`)
- **`MCP_SERVER_NAME`**: Server name (default: `TypeScript`)
- **`NODE_ENV`**: Environment (`production`, `development`)

#### Semantic Caching (Optional)

- **`ENABLE_SEMANTIC_CACHE`**: Enable semantic similarity caching
  (`true`/`false`, default: `false`)
- **`ENABLE_DEDUPLICATION`**: Enable result deduplication (`true`/`false`,
  default: `true`)
- **`CACHE_TTL_SECONDS`**: Cache time-to-live in seconds (default: `3600`)
- **`MAX_RESULTS_PER_DOMAIN`**: Maximum results per domain (default: `2`)

**Note**: Enabling semantic caching requires downloading an embedding model
(~100MB) on first use.

### Feature Flags

Feature flags are controlled via environment variables and validated on server
startup. Check `src/config/featureFlags.ts` for current flags.

## Development

### Project Structure

```
src/
├── index.ts                    # Entry point (imports server)
├── server/
│   └── server.ts              # Main server setup, tool registration, transport
├── tools/
│   ├── braveSearchTools.ts    # Brave Search tool implementations
│   ├── perplexityDeepResearch.ts  # Perplexity Deep Research tool
│   └── winCliTools.ts         # Windows CLI execution tools
├── services/
│   ├── searchService.ts       # Enhanced search service with caching
│   ├── semanticCache.ts       # Semantic similarity caching
│   ├── embeddingService.ts    # Embedding model for semantic search
│   └── resultProcessor.ts     # Result parsing, deduplication, formatting
├── utils/
│   ├── logger.ts              # Structured logging utility
│   ├── config.ts              # Configuration loading
│   ├── validation.ts          # Command and path validation
│   ├── windowsValidation.ts   # Windows-specific security validation
│   ├── translation.ts         # Unix-to-Windows command translation
│   └── directoryManager.ts    # Directory and workspace management
├── config/
│   ├── featureFlags.ts        # Feature flag configuration
│   └── modelConfig.ts         # Model configuration
└── types/
    ├── config.ts              # TypeScript type definitions
    ├── errors.ts              # Error type definitions
    ├── messages.ts            # Message type definitions
    └── winCli.ts              # Windows CLI type definitions
```

### Adding New Tools

1. **Create Tool File:** Create a new file in `src/tools/` (e.g.,
   `myNewTool.ts`):

   ```typescript
   import { z } from 'zod';
   import {
     CallToolResult,
     TextContent,
   } from '@modelcontextprotocol/sdk/types.js';
   import { log } from '../utils/logger.js';

   // Define Zod schema
   export const MyToolZodSchema = z.object({
     param1: z.string().describe('Description for parameter 1'),
     param2: z.number().optional().describe('Optional parameter 2'),
   });

   export type MyToolArgs = z.infer<typeof MyToolZodSchema>;

   // Execution function
   export async function executeMyTool(
     args: MyToolArgs,
   ): Promise<CallToolResult> {
     log('info', `Executing my_tool with: ${args.param1}`);

     try {
       // Your tool logic here
       const result = `Processed: ${args.param1}`;

       return {
         content: [{ type: 'text', text: result } as TextContent],
         isError: false,
       };
     } catch (error) {
       log('error', `Error in my_tool: ${error}`);
       return {
         content: [
           {
             type: 'text',
             text: `Error: ${
               error instanceof Error ? error.message : String(error)
             }`,
           } as TextContent,
         ],
         isError: true,
       };
     }
   }
   ```

2. **Register Tool in Server:** Add to `src/server/server.ts`:

   ```typescript
   import { executeMyTool } from '../tools/myNewTool.js';
   import { MyToolZodSchema } from '../tools/myNewTool.js';

   // Inside main() function, after server initialization:
   log('info', 'Registering tool: my_tool');
   server.registerTool(
     'my_tool',
     {
       description: 'Description of what my tool does',
       inputSchema: MyToolZodSchema,
       annotations: {
         title: 'My Tool',
       },
     },
     async (args) => wrapToolExecution('my_tool', executeMyTool, args),
   );
   ```

3. **Rebuild:**
   ```bash
   npm run build
   ```

### Testing

```bash
# Run TypeScript compiler in watch mode
npm run build -- --watch

# Run server in development mode (auto-restart)
npm run dev

# Check for TypeScript errors
npx tsc --noEmit
```

### Code Quality

```bash
# Format code (if using Prettier)
npx prettier --write "src/**/*.ts"

# Lint code (if using ESLint)
npx eslint "src/**/*.ts"

# Type checking
npx tsc --noEmit
```

## Architecture

### Search Service Architecture

The server uses a layered search service architecture:

1. **SearchService**: High-level interface with transparent caching
2. **Semantic Cache**: Similarity-based caching using embeddings
3. **Result Processor**: Parsing, deduplication, and formatting
4. **Embedding Service**: Vector embeddings for semantic similarity

### Rate Limiting

- **Brave Search**: 1 request/second, 2000 requests/month (free tier)
- **Perplexity**: 2 seconds minimum between requests
- **Retry Logic**: Exponential backoff with jitter for failed requests

### Security Features

- **Command Validation**: Blocks dangerous commands and operators
- **Path Restrictions**: Validates allowed paths for file operations
- **Destructive Command Protection**: Requires `force` flag for dangerous
  operations
- **Shell Operator Validation**: Prevents command injection via operators
- **Command History**: Tracks executed commands (configurable)

### Error Handling

- **Graceful Shutdown**: Signal handlers for SIGINT/SIGTERM
- **Unhandled Exception Handling**: Catches and logs unhandled errors
- **Tool Error Wrapping**: Consistent error formatting for MCP responses
- **Retry Logic**: Automatic retries with exponential backoff

## Troubleshooting

### Server Won't Start

1. **Check Node.js Version:**

   ```bash
   node --version  # Should be 18+
   ```

2. **Verify Dependencies:**

   ```bash
   npm install
   ```

3. **Check Build:**

   ```bash
   npm run build
   ```

   Ensure `dist/server/server.js` exists

4. **Verify API Keys:** Check that `.env` file contains `BRAVE_API_KEY` and
   `PERPLEXITY_API_KEY`

### Tools Not Available

1. **Check Server Logs:** Server logs appear on `stderr`. Look for tool
   registration messages.

2. **Verify Tool Registration:** Check `src/server/server.ts` for tool
   registration calls

3. **Check API Keys:** Missing API keys will cause tools to fail at runtime

### Semantic Cache Issues

1. **Model Download:** First use downloads embedding model (~100MB). Ensure
   internet connection.

2. **Cache Database:** Cache stored in `cache/` directory. Delete to reset
   cache.

3. **Feature Flag:** Ensure `ENABLE_SEMANTIC_CACHE=true` in `.env`

### Rate Limit Errors

- **Brave Search**: Wait 1 second between requests, respect monthly limit
- **Perplexity**: Minimum 2 seconds between requests
- Server includes automatic retry logic with exponential backoff

## License

This project is licensed under the MIT License. Refer to the `LICENSE` file in
the root of the AiChemistForge repository for details.

## Acknowledgments

- Built with
  [`@modelcontextprotocol/sdk`](https://github.com/modelcontextprotocol/typescript-sdk)
  (v1.12.0)
- Uses [Zod](https://zod.dev/) for schema validation
- Semantic caching powered by
  [`@xenova/transformers`](https://github.com/xenova/transformers.js)
- Database operations use
  [`better-sqlite3`](https://github.com/WiseLibs/better-sqlite3)

## Contributing

When contributing:

1. **Follow TypeScript Best Practices**: Use strict mode, proper types
2. **Use Zod for Validation**: All tool inputs should use Zod schemas
3. **Error Handling**: Return `CallToolResult` with `isError` flag
4. **Logging**: Use `log()` utility, output to stderr only
5. **Testing**: Test tools manually before submitting
6. **Documentation**: Update this README for new tools/features
