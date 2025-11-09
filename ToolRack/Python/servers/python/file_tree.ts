// Auto-generated API file for file_tree tool
// Server: python
// Description: Generate a file tree structure from a directory path with comprehensive analysis

import { callMCPTool } from "../client.js";

interface FileTreeInput {
  path?: string;  // Directory path to analyze
  max_depth?: number;  // Maximum depth to traverse
  show_hidden?: boolean;  // Whether to show hidden files
  show_sizes?: boolean;  // Whether to show file sizes
  format?: string;  // Output format: tree, json, or flat
  include_patterns?: string[];
  exclude_patterns?: string[];
  show_tokens?: boolean;  // Whether to show token counts
  show_components?: boolean;  // Whether to show component counts
  llm_optimized?: boolean;  // Whether to optimize for LLM usage
  max_context_tokens?: number;  // Maximum number of tokens
  complexity_filter?: string;  // Filter for complexity levels
}

interface FileTreeResponse {
  success: boolean;
  result?: any;
  error?: string;
  [key: string]: any;
}

/**
 * Generate a file tree structure from a directory path with comprehensive analysis
 *
 * Tool: file_tree
 * Server: python
 */
export async function fileTree(
  input: FileTreeInput
): Promise<FileTreeResponse> {
  return callMCPTool<FileTreeResponse>(
    "python__file_tree",
    input
  );
}
