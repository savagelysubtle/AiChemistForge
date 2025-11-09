import { featureFlags } from '../config/featureFlags.js';
import { logger } from '../utils/logger.js';
import {
  parseSearchResults,
  deduplicateResults,
  formatResults,
  formatCacheAge,
  ProcessedOutput,
} from './resultProcessor.js';
import { semanticCache } from './semanticCache.js';
import { embeddings } from './embeddingService.js';

/**
 * Enhanced search service with transparent caching and processing
 */
export class SearchService {
  private static initialized = false;

  /**
   * Initialize services (call on server startup)
   */
  static async initialize() {
    if (this.initialized) return;

    logger.getMetrics(); // Initialize logger

    if (featureFlags.ENABLE_SEMANTIC_CACHE) {
      try {
        // Initialize embedding model first (downloads if needed)
        await embeddings.initialize();

        // Initialize cache database
        await semanticCache.initialize();

        this.initialized = true;
        logger.getMetrics(); // Log initialization
      } catch (error) {
        logger.getMetrics(); // Log error
        throw error;
      }
    } else {
      this.initialized = true;
    }
  }

  /**
   * Execute search with all enhancements applied transparently
   */
  static async search(
    query: string,
    count: number = 10,
    offset: number = 0,
    searchType: 'web' | 'code' = 'web',
  ): Promise<string> {
    const startTime = Date.now();

    // Check semantic cache first (if enabled)
    if (featureFlags.ENABLE_SEMANTIC_CACHE) {
      const cached = await semanticCache.findSimilar(query, searchType);

      if (cached) {
        const latency = Date.now() - startTime;
        logger.recordCacheHit(latency);

        // Format cached results with cache metadata
        const cachedResults = cached.results;
        const cacheAge = formatCacheAge(cached.timestamp);

        // Replace cache indicator if present, or add it
        if (cachedResults.includes('*Fresh results')) {
          return cachedResults.replace(
            '*Fresh results',
            `*Results from cache (${cacheAge})`,
          );
        } else if (cachedResults.includes('*Results from cache')) {
          // Already has cache indicator, just update the age
          return cachedResults.replace(
            /\*Results from cache \([^)]+\)/,
            `*Results from cache (${cacheAge})`,
          );
        } else {
          // No cache indicator, add it at the beginning
          return `*Results from cache (${cacheAge}) - ${latency}ms*\n\n${cachedResults}`;
        }
      }
    }

    // Cache miss - execute search (dynamic import to avoid circular dependency)
    const { performBraveSearch } = await import('../tools/braveSearchTools.js');
    const rawResults = await performBraveSearch(query, count, offset);
    const latency = Date.now() - startTime;

    // Parse and process
    let results = parseSearchResults(rawResults);

    // Apply deduplication
    results = deduplicateResults(results);

    // Format output
    const processed: ProcessedOutput = {
      results,
      metadata: {
        query,
        count: results.length,
        cached: false,
        latencyMs: latency,
      },
    };

    const formatted = formatResults(processed);

    logger.recordCacheMiss(latency);

    // Store in cache for future queries
    if (featureFlags.ENABLE_SEMANTIC_CACHE) {
      await semanticCache.store(query, searchType, formatted);
    }

    return formatted;
  }
}

