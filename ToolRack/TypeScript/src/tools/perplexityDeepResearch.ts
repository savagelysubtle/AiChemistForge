import { z } from 'zod';
import { CallToolResult, TextContent } from '@modelcontextprotocol/sdk/types.js';

// Zod schema for input validation
export const PerplexityDeepResearchZodSchema = z.object({
  query: z
    .string()
    .min(10, 'Query must be at least 10 characters')
    .max(2000, 'Query cannot exceed 2000 characters')
    .describe('Research query or topic for comprehensive analysis'),
  search_recency_filter: z
    .enum(['month', 'week', 'day', 'hour'])
    .optional()
    .describe('Filter sources by recency (optional)'),
  return_images: z
    .boolean()
    .default(false)
    .optional()
    .describe('Include relevant images in response'),
  return_related_questions: z
    .boolean()
    .default(false)
    .optional()
    .describe('Include related research questions'),
});

export type PerplexityDeepResearchArgs = z.infer<
  typeof PerplexityDeepResearchZodSchema
>;

// API configuration
const PERPLEXITY_API_KEY = process.env.PERPLEXITY_API_KEY;
const API_ENDPOINT = 'https://api.perplexity.ai/chat/completions';
const TIMEOUT_MS = 600000; // 10 minutes for deep research

// Validate API key on module load
if (!PERPLEXITY_API_KEY) {
  console.error(
    '[Perplexity] WARNING: PERPLEXITY_API_KEY environment variable is not set. Tool will fail at runtime.',
  );
}

// Retry configuration (similar to Brave Search pattern)
const RETRY_CONFIG = {
  maxAttempts: 3,
  initialDelayMs: 2000,
  maxDelayMs: 15000,
  backoffMultiplier: 2,
  jitterFactor: 0.1,
};

function addJitter(delayMs: number): number {
  const jitter =
    delayMs * RETRY_CONFIG.jitterFactor * (Math.random() - 0.5);
  return Math.round(delayMs + jitter);
}

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Formats research results with citations for MCP response
 */
function formatResearchResults(
  content: string,
  citations?: string[],
  relatedQuestions?: string[],
): string {
  let formatted = `# Deep Research Report\n\n${content}`;

  if (citations && citations.length > 0) {
    formatted += '\n\n## Citations\n\n';
    citations.forEach((citation, idx) => {
      formatted += `[${idx + 1}] ${citation}\n`;
    });
  } else {
    formatted +=
      '\n\n## Note\n\nCitations were requested but not provided by the API.';
  }

  if (relatedQuestions && relatedQuestions.length > 0) {
    formatted += '\n\n## Related Questions\n\n';
    relatedQuestions.forEach((question, idx) => {
      formatted += `${idx + 1}. ${question}\n`;
    });
  }

  return formatted;
}

/**
 * Tracks rate limiting to prevent API throttling
 */
const lastRequestTime = { value: 0 };
const MIN_REQUEST_INTERVAL_MS = 2000; // 2 seconds between requests

async function enforceRateLimit(): Promise<void> {
  const now = Date.now();
  const timeSinceLastRequest = now - lastRequestTime.value;

  if (timeSinceLastRequest < MIN_REQUEST_INTERVAL_MS) {
    const waitTime = MIN_REQUEST_INTERVAL_MS - timeSinceLastRequest;
    console.error(
      `[Perplexity] Rate limiting: waiting ${waitTime}ms before request`,
    );
    await sleep(waitTime);
  }

  lastRequestTime.value = Date.now();
}

/**
 * Core deep research execution with retry logic
 */
async function performDeepResearch(
  args: PerplexityDeepResearchArgs,
): Promise<string> {
  if (!PERPLEXITY_API_KEY) {
    throw new Error(
      'PERPLEXITY_API_KEY environment variable is required but not set',
    );
  }

  // Enforce rate limiting
  await enforceRateLimit();

  let attempt = 0;
  let lastError: Error | null = null;

  while (attempt < RETRY_CONFIG.maxAttempts) {
    attempt++;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
      console.error(
        `[Perplexity] Starting deep research (attempt ${attempt}/${RETRY_CONFIG.maxAttempts})`,
      );
      console.error(`[Perplexity] Query: "${args.query.substring(0, 100)}..."`);

      const startTime = Date.now();

      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          Authorization: `Bearer ${PERPLEXITY_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'sonar-deep-research',
          messages: [
            {
              role: 'user',
              content: args.query,
            },
          ],
          temperature: 0.2, // Lower temperature for factual research
          ...(args.search_recency_filter && {
            search_recency_filter: args.search_recency_filter,
          }),
          return_images: args.return_images ?? false,
          return_related_questions: args.return_related_questions ?? false,
          return_citations: true, // Always include citations
        }),
      });

      clearTimeout(timeoutId);

      const elapsed = Date.now() - startTime;

      // Handle rate limiting (429)
      if (response.status === 429) {
        const retryAfter = response.headers.get('retry-after');
        const retryDelayMs = retryAfter
          ? parseInt(retryAfter) * 1000
          : Math.min(
              RETRY_CONFIG.initialDelayMs *
                Math.pow(RETRY_CONFIG.backoffMultiplier, attempt - 1),
              RETRY_CONFIG.maxDelayMs,
            );

        lastError = new Error(
          `Rate limit exceeded (429). Attempt ${attempt}/${RETRY_CONFIG.maxAttempts}`,
        );
        console.error(`[Perplexity] ${lastError.message}`);

        if (attempt < RETRY_CONFIG.maxAttempts) {
          const waitTime = addJitter(retryDelayMs);
          console.error(`[Perplexity] Waiting ${waitTime}ms before retry...`);
          await sleep(waitTime);
          continue;
        } else {
          throw new Error(
            `Rate limit exceeded after ${RETRY_CONFIG.maxAttempts} attempts`,
          );
        }
      }

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Perplexity API error: ${response.status} ${response.statusText}. Details: ${errorText}`,
        );
      }

      const data = await response.json();

      // Extract content and citations
      const content =
        data.choices?.[0]?.message?.content || 'No research results returned';
      const citations = data.citations || [];
      const relatedQuestions = data.related_questions || [];

      console.error(
        `[Perplexity] Research completed successfully in ${elapsed}ms (${citations.length} citations)`,
      );

      return formatResearchResults(content, citations, relatedQuestions);
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error && error.name === 'AbortError') {
        lastError = new Error(
          `Request timeout after ${TIMEOUT_MS}ms. Attempt ${attempt}/${RETRY_CONFIG.maxAttempts}`,
        );
        console.error(`[Perplexity] ${lastError.message}`);

        if (attempt < RETRY_CONFIG.maxAttempts) {
          const waitTime = addJitter(
            RETRY_CONFIG.initialDelayMs *
              Math.pow(RETRY_CONFIG.backoffMultiplier, attempt - 1),
          );
          console.error(`[Perplexity] Waiting ${waitTime}ms before retry...`);
          await sleep(waitTime);
          continue;
        }
      }

      // For other errors, check if we should retry
      if (
        error instanceof Error &&
        (error.message.includes('ECONNRESET') ||
          error.message.includes('ETIMEDOUT') ||
          error.message.includes('network'))
      ) {
        lastError = error;
        if (attempt < RETRY_CONFIG.maxAttempts) {
          const waitTime = addJitter(
            RETRY_CONFIG.initialDelayMs *
              Math.pow(RETRY_CONFIG.backoffMultiplier, attempt - 1),
          );
          console.error(
            `[Perplexity] Network error, waiting ${waitTime}ms before retry...`,
          );
          await sleep(waitTime);
          continue;
        }
      }

      // For other errors, don't retry - throw immediately
      throw error;
    }
  }

  throw (
    lastError || new Error('Deep research failed after maximum retry attempts')
  );
}

/**
 * Exported execution function for MCP tool registration
 */
export async function executeDeepResearch(
  args: PerplexityDeepResearchArgs,
): Promise<CallToolResult> {
  try {
    console.error(
      `[Perplexity] Executing deep research tool with query length: ${args.query.length}`,
    );

    const resultsText = await performDeepResearch(args);

    return {
      content: [{ type: 'text', text: resultsText } as TextContent],
      isError: false,
    };
  } catch (error) {
    console.error('[Perplexity] Error during deep research:', error);
    return {
      content: [
        {
          type: 'text',
          text: `Deep research failed: ${error instanceof Error ? error.message : String(error)}`,
        } as TextContent,
      ],
      isError: true,
    };
  }
}


