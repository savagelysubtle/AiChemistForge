// Auto-generated API file for codebase_ingest tool
// Server: python
// Description: Ingest entire codebase as structured text for LLM context

import { callMCPTool } from "../client.js";

interface CodebaseIngestInput {
  path?: string;  // Root directory path to ingest
  max_file_size?: number;  // Maximum file size in bytes
  include_binary?: boolean;  // Whether to attempt reading binary files
  output_format?: string;  // Output format: structured or markdown
  include_patterns?: string[];
  exclude_patterns?: string[];
  show_tree?: boolean;  // Whether to include directory tree
  max_files?: number;  // Maximum number of files to process
  encoding?: string;  // Text encoding to use
  max_context_tokens?: number;  // Maximum number of tokens
  chunk_strategy?: string;  // Strategy for chunking files
  include_components?: boolean;  // Whether to include file components
  include_complexity?: boolean;  // Whether to include file complexity
  llm_optimized?: boolean;  // Whether to optimize for LLM context
}

interface CodebaseIngestResponse {
  success: boolean;
  result?: any;
  error?: string;
  [key: string]: any;
}

/**
 * Ingest entire codebase as structured text for LLM context
 *
 * Tool: codebase_ingest
 * Server: python
 */
export async function codebaseIngest(
  input: CodebaseIngestInput
): Promise<CodebaseIngestResponse> {
  return callMCPTool<CodebaseIngestResponse>(
    "python__codebase_ingest",
    input
  );
}
