// Auto-generated API file for sequential_think tool
// Server: python
// Description: Break down problem into sequential thinking steps

import { callMCPTool } from "../client.js";

interface SequentialThinkInput {
  problem: string;  // The problem to analyze and solve
  context?: string;  // Additional context or constraints
  approach?: string;  // Thinking approach: systematic, creative, analytical, practical
}

interface SequentialThinkResponse {
  success: boolean;
  result?: any;
  error?: string;
  [key: string]: any;
}

/**
 * Break down problem into sequential thinking steps
 *
 * Tool: sequential_think
 * Server: python
 */
export async function sequentialThink(
  input: SequentialThinkInput
): Promise<SequentialThinkResponse> {
  return callMCPTool<SequentialThinkResponse>(
    "python__sequential_think",
    input
  );
}
