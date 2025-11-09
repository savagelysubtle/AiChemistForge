import Database from 'better-sqlite3';
import { embeddings, cosineSimilarity } from './embeddingService.js';
import { featureFlags } from '../config/featureFlags.js';
import { MODEL_CONFIG } from '../config/modelConfig.js';
import { log } from '../utils/logger.js';
import * as fs from 'fs';
import * as path from 'path';

interface CacheEntry {
  id: number;
  query: string;
  query_embedding: Buffer;
  results: string;
  search_type: string;
  timestamp: number;
  ttl: number;
}

interface CacheHit {
  results: string;
  timestamp: number;
  query: string;
  similarity: number;
}

class SemanticCacheService {
  private db: Database.Database | null = null;
  private readonly dbPath = MODEL_CONFIG.cache.dbPath;
  private readonly similarityThreshold = MODEL_CONFIG.cache.similarityThreshold;

  /**
   * Initialize database and create tables
   */
  async initialize(): Promise<void> {
    if (this.db) return;

    try {
      // Ensure cache directory exists
      const cacheDir = path.dirname(this.dbPath);
      if (!fs.existsSync(cacheDir)) {
        fs.mkdirSync(cacheDir, { recursive: true });
      }

      // Open database
      this.db = new Database(this.dbPath);
      this.db.pragma('journal_mode = WAL'); // Enable Write-Ahead Logging for concurrency

      // Create table
      this.db.exec(`
        CREATE TABLE IF NOT EXISTS search_cache (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          query TEXT NOT NULL,
          query_embedding BLOB NOT NULL,
          results TEXT NOT NULL,
          search_type TEXT NOT NULL,
          timestamp INTEGER NOT NULL,
          ttl INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_timestamp ON search_cache(timestamp);
        CREATE INDEX IF NOT EXISTS idx_search_type ON search_cache(search_type);
      `);

      log('info', '[Cache] Initialized successfully', {
        path: this.dbPath,
        entries: this.getSize(),
      });
    } catch (error) {
      log('error', '[Cache] Failed to initialize', { error });
      throw error;
    }
  }

  /**
   * Find similar cached query
   */
  async findSimilar(
    query: string,
    searchType: string,
  ): Promise<CacheHit | null> {
    if (!this.db) await this.initialize();

    try {
      // Generate embedding for query
      const queryEmbedding = await embeddings.embed(query);

      // Clean up expired entries first
      this.cleanupExpired();

      // Get all entries of the same search type (for now, linear scan)
      // TODO: In future, use sqlite-vec for true vector indexing
      const stmt = this.db!.prepare(`
        SELECT id, query, query_embedding, results, timestamp, ttl
        FROM search_cache
        WHERE search_type = ?
        ORDER BY timestamp DESC
        LIMIT 100
      `);

      const entries = stmt.all(searchType) as CacheEntry[];

      let bestMatch: CacheHit | null = null;
      let bestSimilarity = 0;

      for (const entry of entries) {
        // Convert Buffer to Float32Array
        const cachedEmbedding = new Float32Array(
          new Uint8Array(entry.query_embedding).buffer,
        );

        const similarity = cosineSimilarity(queryEmbedding, cachedEmbedding);

        if (
          similarity > bestSimilarity &&
          similarity >= this.similarityThreshold
        ) {
          bestSimilarity = similarity;
          bestMatch = {
            results: entry.results,
            timestamp: entry.timestamp,
            query: entry.query,
            similarity,
          };
        }
      }

      if (bestMatch) {
        log('info', `[Cache] HIT - Similarity: ${bestMatch.similarity.toFixed(3)}`, {
          cachedQuery: bestMatch.query,
          currentQuery: query,
        });
      }

      return bestMatch;
    } catch (error) {
      log('error', '[Cache] Error finding similar query', { error });
      return null;
    }
  }

  /**
   * Store query and results in cache
   */
  async store(
    query: string,
    searchType: string,
    results: string,
    ttlSeconds: number = featureFlags.CACHE_TTL_SECONDS,
  ): Promise<void> {
    if (!this.db) await this.initialize();

    try {
      // Generate embedding
      const queryEmbedding = await embeddings.embed(query);

      // Convert Float32Array to Buffer
      const embeddingBuffer = Buffer.from(queryEmbedding.buffer);

      const stmt = this.db!.prepare(`
        INSERT INTO search_cache (query, query_embedding, results, search_type, timestamp, ttl)
        VALUES (?, ?, ?, ?, ?, ?)
      `);

      stmt.run(
        query,
        embeddingBuffer,
        results,
        searchType,
        Date.now(),
        ttlSeconds * 1000,
      );

      log('info', '[Cache] Stored new entry', {
        query,
        searchType,
        ttlSeconds,
      });
    } catch (error) {
      log('error', '[Cache] Failed to store entry', { error });
      // Don't throw - caching failure shouldn't break search
    }
  }

  /**
   * Clean up expired cache entries
   */
  private cleanupExpired(): void {
    if (!this.db) return;

    try {
      const now = Date.now();
      const stmt = this.db.prepare(`
        DELETE FROM search_cache
        WHERE timestamp + ttl < ?
      `);

      const result = stmt.run(now);

      if (result.changes > 0) {
        log('info', `[Cache] Cleaned up ${result.changes} expired entries`);
      }
    } catch (error) {
      log('error', '[Cache] Failed to cleanup', { error });
    }
  }

  /**
   * Get cache size
   */
  getSize(): number {
    if (!this.db) return 0;

    try {
      const stmt = this.db.prepare('SELECT COUNT(*) as count FROM search_cache');
      const result = stmt.get() as { count: number };
      return result.count;
    } catch {
      return 0;
    }
  }

  /**
   * Clear all cache
   */
  clear(): void {
    if (!this.db) return;

    try {
      this.db.prepare('DELETE FROM search_cache').run();
      log('info', '[Cache] Cleared all entries');
    } catch (error) {
      log('error', '[Cache] Failed to clear', { error });
    }
  }

  /**
   * Close database connection
   */
  close(): void {
    if (this.db) {
      this.db.close();
      this.db = null;
      log('info', '[Cache] Database closed');
    }
  }
}

// Singleton instance
export const semanticCache = new SemanticCacheService();

