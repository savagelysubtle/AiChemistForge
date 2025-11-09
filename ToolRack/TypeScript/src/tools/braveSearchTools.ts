// import { log } from '../../../brave-search/src/logger.js'; // Import the logger
import { z } from 'zod'; // Import Zod

console.error('[TOOLS.TS] Module start.'); // Use console.error
console.error(
  `[TOOLS.TS] BRAVE_API_KEY in process.env at module start: ${
    process.env.BRAVE_API_KEY ? 'Exists' : 'DOES NOT EXIST'
  }`,
); // Use console.error

import {
  CallToolResult,
  TextContent, // For return type
} from '@modelcontextprotocol/sdk/types.js';

// Import SearchService and validate feature flags
import { SearchService } from '../services/searchService.js';
import { validateFeatureFlags } from '../config/featureFlags.js';

// Validate feature flags on module load
validateFeatureFlags();

// Define Zod Schemas for tool inputs
export const BraveWebSearchZodSchema = z.object({
  query: z.string().describe('Search query (max 400 chars, 50 words)'),
  count: z
    .number()
    .default(10)
    .describe('Number of results (1-20, default 10)')
    .optional(),
  offset: z
    .number()
    .default(0)
    .describe('Pagination offset (max 9, default 0)')
    .optional(),
});

export const BraveCodeSearchZodSchema = z.object({
  query: z
    .string()
    .describe("Code search query (e.g. 'github repository for brave search')"),
  count: z
    .number()
    .default(10)
    .describe('Number of results (1-20, default 10)')
    .optional(),
});

// Check for API key - this needs to be accessible by the execution logic.
// It's fine for it to be a module-level constant checked once.
console.error('[TOOLS.TS] About to check BRAVE_API_KEY value.'); // Use console.error
const BRAVE_API_KEY = process.env.BRAVE_API_KEY!;
if (!BRAVE_API_KEY) {
  // Log to stderr and throw to prevent the module from being used incorrectly if key is missing
  console.error(
    'CRITICAL: BRAVE_API_KEY environment variable is required for braveSearchTools module.',
  ); // Use console.error
  throw new Error('BRAVE_API_KEY environment variable is required.');
}

// Brave API Free Tier Limits (confirmed from official docs)
const RATE_LIMIT = {
  perSecond: 1,
  perMonth: 2000, // Free tier limit
};

// Retry configuration
const RETRY_CONFIG = {
  maxAttempts: 3, // Maximum retry attempts
  initialDelayMs: 1000, // Start with 1 second delay
  maxDelayMs: 10000, // Cap at 10 seconds
  backoffMultiplier: 2, // Exponential backoff multiplier
  jitterFactor: 0.1, // 10% random jitter to avoid thundering herd
};

let requestCount = {
  second: 0,
  month: 0,
  lastSecondReset: Date.now(),
  lastMonthReset: Date.now(),
};

/**
 * Checks if we're within rate limits. If at limit, calculates wait time.
 * @returns Object with canProceed flag and waitTimeMs if we need to wait
 */
function checkRateLimit(): {
  canProceed: boolean;
  waitTimeMs: number;
  reason?: string;
} {
  const now = Date.now();

  // Reset per-second counter if more than 1 second has passed
  if (now - requestCount.lastSecondReset >= 1000) {
    requestCount.second = 0;
    requestCount.lastSecondReset = now;
  }

  // Reset monthly counter (30 days = 2,592,000,000 ms)
  if (now - requestCount.lastMonthReset >= 2592000000) {
    requestCount.month = 0;
    requestCount.lastMonthReset = now;
  }

  // Check monthly limit first (hard limit)
  if (requestCount.month >= RATE_LIMIT.perMonth) {
    return {
      canProceed: false,
      waitTimeMs: 0, // Can't retry, need to wait until next month
      reason: `Monthly rate limit of ${
        RATE_LIMIT.perMonth
      } requests exceeded. Resets in ${Math.ceil(
        (2592000000 - (now - requestCount.lastMonthReset)) / 86400000,
      )} days.`,
    };
  }

  // Check per-second limit (can retry after waiting)
  if (requestCount.second >= RATE_LIMIT.perSecond) {
    const waitTime = 1000 - (now - requestCount.lastSecondReset);
    return {
      canProceed: false,
      waitTimeMs: Math.max(0, waitTime),
      reason: `Per-second rate limit reached. Wait ${waitTime}ms before retry.`,
    };
  }

  return { canProceed: true, waitTimeMs: 0 };
}

/**
 * Increments rate limit counters after successful API call
 */
function incrementRateLimit(): void {
  requestCount.second++;
  requestCount.month++;
}

/**
 * Adds jitter to delay to avoid thundering herd problem
 * @param delayMs Base delay in milliseconds
 * @returns Delay with jitter applied
 */
function addJitter(delayMs: number): number {
  const jitter = delayMs * RETRY_CONFIG.jitterFactor * (Math.random() - 0.5);
  return Math.round(delayMs + jitter);
}

/**
 * Waits for specified milliseconds
 * @param ms Milliseconds to wait
 */
async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Inferred types for function signatures
export type BraveWebSearchArgs = z.infer<typeof BraveWebSearchZodSchema>;
export type BraveCodeSearchArgs = z.infer<typeof BraveCodeSearchZodSchema>;

interface BraveWeb {
  web?: {
    results?: Array<{
      title: string;
      description: string;
      url: string;
      language?: string;
      published?: string;
      rank?: number;
    }>;
  };
  // locations part can be removed if local search is fully gone
}

/**
 * Core search logic with exponential backoff retry mechanism.
 * Handles rate limiting, retries on 429 errors, and respects Brave API limits.
 * @param query Search query string
 * @param count Number of results to return (1-20)
 * @param offset Pagination offset (0-9)
 * @returns Formatted search results as a string
 */
export async function performBraveSearch(
  query: string,
  count: number = 10,
  offset: number = 0,
): Promise<string> {
  let attempt = 0;
  let lastError: Error | null = null;

  while (attempt < RETRY_CONFIG.maxAttempts) {
    attempt++;

    // Check rate limit before attempting request
    const rateLimitCheck = checkRateLimit();

    if (!rateLimitCheck.canProceed) {
      // If monthly limit exceeded, don't retry
      if (rateLimitCheck.waitTimeMs === 0) {
        throw new Error(
          rateLimitCheck.reason || 'Monthly rate limit exceeded.',
        );
      }

      // For per-second limit, wait and retry
      console.error(
        `[Brave Search] Rate limit check failed on attempt ${attempt}. ${rateLimitCheck.reason}`,
      );

      if (attempt < RETRY_CONFIG.maxAttempts) {
        const waitTime = addJitter(rateLimitCheck.waitTimeMs);
        console.error(
          `[Brave Search] Waiting ${waitTime}ms before retry ${attempt + 1}/${
            RETRY_CONFIG.maxAttempts
          }...`,
        );
        await sleep(waitTime);
        continue; // Retry without incrementing attempt
      }
    }

    const url = new URL('https://api.search.brave.com/res/v1/web/search');
    url.searchParams.set('q', query);
    url.searchParams.set('count', Math.min(count, 20).toString()); // API limit
    url.searchParams.set('offset', Math.max(0, Math.min(offset, 9)).toString()); // API limits for offset

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    try {
      const response = await fetch(url, {
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          'Accept-Encoding': 'gzip',
          'X-Subscription-Token': BRAVE_API_KEY,
        },
      });

      // Handle rate limit response from API
      if (response.status === 429) {
        clearTimeout(timeoutId);

        // Extract retry-after header if available
        const retryAfter = response.headers.get('retry-after');
        const retryDelayMs = retryAfter
          ? parseInt(retryAfter) * 1000
          : Math.min(
              RETRY_CONFIG.initialDelayMs *
                Math.pow(RETRY_CONFIG.backoffMultiplier, attempt - 1),
              RETRY_CONFIG.maxDelayMs,
            );

        lastError = new Error(
          `Brave API rate limit exceeded (429). Attempt ${attempt}/${RETRY_CONFIG.maxAttempts}`,
        );
        console.error(`[Brave Search] ${lastError.message}`);

        if (attempt < RETRY_CONFIG.maxAttempts) {
          const waitTime = addJitter(retryDelayMs);
          console.error(`[Brave Search] Waiting ${waitTime}ms before retry...`);
          await sleep(waitTime);
          continue;
        } else {
          throw new Error(
            `Brave API rate limit exceeded after ${RETRY_CONFIG.maxAttempts} attempts. Please wait before retrying.`,
          );
        }
      }

      if (!response.ok) {
        clearTimeout(timeoutId);
        throw new Error(
          `Brave API error: ${response.status} ${
            response.statusText
          }. Details: ${await response.text()}`,
        );
      }

      const data = (await response.json()) as BraveWeb;

      // Success - increment rate limit counter
      incrementRateLimit();

      const results = (data.web?.results || []).map((result) => ({
        title: result.title || 'N/A', // Provide fallback for missing fields
        description: result.description || 'N/A',
        url: result.url || '#',
      }));

      clearTimeout(timeoutId);

      if (results.length === 0) {
        return 'No results found for your query.';
      }

      return results
        .map(
          (r) =>
            `Title: ${r.title}
Description: ${r.description}
URL: ${r.url}`,
        )
        .join('\n\n');
    } catch (error) {
      clearTimeout(timeoutId);

      // If it's an abort error, it's likely a timeout
      if (error instanceof Error && error.name === 'AbortError') {
        lastError = new Error(
          `Request timeout after 10 seconds. Attempt ${attempt}/${RETRY_CONFIG.maxAttempts}`,
        );
        console.error(`[Brave Search] ${lastError.message}`);

        if (attempt < RETRY_CONFIG.maxAttempts) {
          const waitTime = addJitter(
            RETRY_CONFIG.initialDelayMs *
              Math.pow(RETRY_CONFIG.backoffMultiplier, attempt - 1),
          );
          console.error(`[Brave Search] Waiting ${waitTime}ms before retry...`);
          await sleep(waitTime);
          continue;
        }
      }

      // For other errors, don't retry - throw immediately
      throw error;
    }
  }

  // If we exhausted all retries, throw the last error
  throw lastError || new Error('Search failed after maximum retry attempts');
}

// Exported execution function for Web Search
export async function executeWebSearch(
  args: BraveWebSearchArgs,
): Promise<CallToolResult> {
  const { query, count = 10, offset = 0 } = args;
  try {
    const resultsText = await SearchService.search(query, count, offset, 'web');
    return {
      content: [{ type: 'text', text: resultsText } as TextContent],
      isError: false,
    };
  } catch (error) {
    console.error('Error during web search', {
      query,
      count,
      offset,
      error,
    }); // Log error context
    return {
      content: [
        {
          type: 'text',
          text: `Error during web search: ${
            error instanceof Error ? error.message : String(error)
          }`,
        } as TextContent,
      ],
      isError: true,
    };
  }
}

// Exported execution function for Code Search
export async function executeCodeSearch(
  args: BraveCodeSearchArgs,
): Promise<CallToolResult> {
  const { query: userQuery, count = 10 } = args;

  const siteFilters = [
    'site:stackoverflow.com',
    'site:github.com',
    'site:developer.mozilla.org',
    'site:*.stackexchange.com', // Broader Stack Exchange
    'site:reddit.com/r/programming',
    'site:reddit.com/r/learnprogramming',
    'site:dev.to',
    'site:medium.com', // Often has technical articles
    // Consider official documentation sites for popular languages/frameworks if desired
    // e.g., site:docs.python.org, site:reactjs.org
  ].join(' OR ');

  const finalQuery = `${userQuery} (${siteFilters})`;

  try {
    // Using offset 0 for code search as complex site filters might not paginate predictably
    const resultsText = await SearchService.search(finalQuery, count, 0, 'code');
    return {
      content: [{ type: 'text', text: resultsText } as TextContent],
      isError: false,
    };
  } catch (error) {
    console.error('Error during code search', {
      finalQuery,
      count,
      error,
    }); // Log error context
    return {
      content: [
        {
          type: 'text',
          text: `Error during code search: ${
            error instanceof Error ? error.message : String(error)
          }`,
        } as TextContent,
      ],
      isError: true,
    };
  }
}

// New Zod schema for multi-link search input
export const BraveMultiLinkSearchZodSchema = z.object({
  queries: z.array(
    z
      .string()
      .min(1)
      .max(400)
      .describe(
        'Array of search queries or links (1-10 items, each max 400 chars). Searches are executed sequentially to respect rate limits.',
      ),
  ),
  count: z
    .number()
    .min(1)
    .max(20)
    .default(10)
    .describe('Number of results per query (1-20, default 10)')
    .optional(),
});

// Inferred type for the new schema
export type BraveMultiLinkSearchArgs = z.infer<
  typeof BraveMultiLinkSearchZodSchema
>;

/**
 * Helper function for per-query searches (delegates to performBraveSearch with retry logic).
 * Used by multi-link search to maintain consistent error handling.
 * @param query Search query string
 * @param count Number of results (1-20)
 * @param offset Pagination offset (0-9)
 * @returns Formatted search results or error message
 */
async function performBraveSearchForQuery(
  query: string,
  count: number = 10,
  offset: number = 0,
): Promise<string> {
  try {
    // Delegate to main performBraveSearch which has retry logic
    return await performBraveSearch(query, count, offset);
  } catch (error) {
    // Return error as string to allow multi-link search to continue with other queries
    return `Error searching for query "${query}": ${
      error instanceof Error ? error.message : String(error)
    }`;
  }
}

/**
 * Executes a multi-link search for an array of queries, performing searches sequentially and aggregating results.
 * Sequential execution respects the 1 req/sec rate limit of Brave's free tier.
 * @param args The input arguments, including an array of queries and optional count per query.
 * @returns A CallToolResult with combined search results or an error message.
 */
export async function executeMultiLinkSearch(
  args: BraveMultiLinkSearchArgs,
): Promise<CallToolResult> {
  const { queries, count = 10 } = args;

  if (queries.length === 0) {
    return {
      content: [
        {
          type: 'text',
          text: 'No queries provided for multi-link search.',
        } as TextContent,
      ],
      isError: true,
    };
  }

  if (queries.length > 10) {
    return {
      content: [
        {
          type: 'text',
          text: 'Maximum of 10 queries allowed for multi-link search to respect API limits.',
        } as TextContent,
      ],
      isError: true,
    };
  }

  // Validate each query length
  for (const query of queries) {
    if (query.length > 400) {
      return {
        content: [
          {
            type: 'text',
            text: `Query "${query}" exceeds 400 characters. Please shorten it.`,
          } as TextContent,
        ],
        isError: true,
      };
    }
  }

  try {
    // Execute searches sequentially to better respect rate limits
    // With 1 req/sec limit, concurrent execution would trigger rate limiting
    const searchResults: string[] = [];

    console.error(
      `[Multi-Link Search] Processing ${queries.length} queries sequentially to respect rate limits...`,
    );

    for (let i = 0; i < queries.length; i++) {
      const query = queries[i];
      console.error(
        `[Multi-Link Search] Query ${i + 1}/${queries.length}: "${query}"`,
      );

      const results = await performBraveSearchForQuery(query, count, 0);
      searchResults.push(
        `Results for Query ${i + 1} ("${query}"):\n${results}`,
      );

      // Add small delay between queries to ensure we stay under rate limit
      // (only if there are more queries to process)
      if (i < queries.length - 1) {
        await sleep(1100); // 1.1 seconds to be safe with 1 req/sec limit
      }
    }

    // Combine results into a single output
    const combinedOutput = searchResults.join('\n\n---\n\n');

    return {
      content: [{ type: 'text', text: combinedOutput } as TextContent],
      isError: false,
    };
  } catch (error) {
    console.error('Error during multi-link search', { queries, count, error }); // Log error context
    return {
      content: [
        {
          type: 'text',
          text: `Unexpected error during multi-link search: ${
            error instanceof Error ? error.message : String(error)
          }`,
        } as TextContent,
      ],
      isError: true,
    };
  }
}
