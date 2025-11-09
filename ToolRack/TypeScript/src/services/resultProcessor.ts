import { featureFlags } from '../config/featureFlags.js';
import { log } from '../utils/logger.js';

export interface SearchResult {
  title: string;
  description: string;
  url: string;
}

export interface ProcessedOutput {
  results: SearchResult[];
  metadata: {
    query: string;
    count: number;
    cached: boolean;
    latencyMs: number;
    cacheAge?: string;
  };
}

/**
 * Parse raw Brave search results text into structured array
 */
export function parseSearchResults(rawText: string): SearchResult[] {
  const results: SearchResult[] = [];

  // Split by double newline (result separator)
  const resultBlocks = rawText.split('\n\n').filter((b) => b.trim());

  for (const block of resultBlocks) {
    const lines = block.split('\n');
    const result: Partial<SearchResult> = {};

    for (const line of lines) {
      if (line.startsWith('Title: ')) {
        result.title = line.substring(7).trim();
      } else if (line.startsWith('Description: ')) {
        result.description = line.substring(13).trim();
      } else if (line.startsWith('URL: ')) {
        result.url = line.substring(5).trim();
      }
    }

    if (result.title && result.url) {
      results.push(result as SearchResult);
    }
  }

  return results;
}

/**
 * Deduplicate results by domain, keeping max N per domain
 */
export function deduplicateResults(
  results: SearchResult[],
  maxPerDomain: number = featureFlags.MAX_RESULTS_PER_DOMAIN,
): SearchResult[] {
  if (!featureFlags.ENABLE_DEDUPLICATION) {
    return results;
  }

  const domainCounts = new Map<string, number>();
  const deduplicated: SearchResult[] = [];

  for (const result of results) {
    try {
      const domain = new URL(result.url).hostname.replace('www.', '');
      const count = domainCounts.get(domain) || 0;

      if (count < maxPerDomain) {
        deduplicated.push(result);
        domainCounts.set(domain, count + 1);
      }
    } catch (error) {
      // Invalid URL, skip
      log('error', 'Invalid URL in result', { url: result.url });
    }
  }

  const removed = results.length - deduplicated.length;
  if (removed > 0) {
    log('info', `Deduplication removed ${removed} results`);
  }

  return deduplicated;
}

/**
 * Format results as enhanced markdown
 */
export function formatResults(processed: ProcessedOutput): string {
  const { results, metadata } = processed;

  if (results.length === 0) {
    return 'No results found for your query.';
  }

  // Header with metadata
  let output = `# Search Results for "${metadata.query}" (${results.length} results)\n\n`;

  if (metadata.cached) {
    output += `*Results from cache (${metadata.cacheAge || 'fresh'}) - ${metadata.latencyMs}ms*\n\n`;
  } else {
    output += `*Fresh results - ${metadata.latencyMs}ms*\n\n`;
  }

  output += '---\n\n';

  // Individual results
  results.forEach((result, index) => {
    const domain = extractDomain(result.url);

    output += `## ${index + 1}. ${result.title}\n`;
    output += `**Source**: ${domain} | **URL**: ${result.url}\n\n`;
    output += `${result.description}\n\n`;
    output += '---\n\n';
  });

  return output;
}

/**
 * Extract domain from URL
 */
function extractDomain(url: string): string {
  try {
    return new URL(url).hostname.replace('www.', '');
  } catch {
    return 'unknown';
  }
}

/**
 * Format cache age timestamp
 */
export function formatCacheAge(timestamp: number): string {
  const ageMs = Date.now() - timestamp;
  const ageMinutes = Math.floor(ageMs / 60000);

  if (ageMinutes < 1) return 'just now';
  if (ageMinutes < 60) return `${ageMinutes}m ago`;

  const ageHours = Math.floor(ageMinutes / 60);
  if (ageHours < 24) return `${ageHours}h ago`;

  const ageDays = Math.floor(ageHours / 24);
  return `${ageDays}d ago`;
}

