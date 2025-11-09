// src/logger.ts
// Simple logger implementation for stderr output
export function log(level: 'info' | 'warn' | 'error', message: string, metadata?: any) {
  const timestamp = new Date().toISOString();
  console.error(`[${timestamp}] [${level.toUpperCase()}] ${message}`, metadata ? JSON.stringify(metadata) : '');
}

/**
 * Metrics tracking for search service
 */
class MCPLogger {
  private metrics = {
    totalQueries: 0,
    cacheHits: 0,
    cacheMisses: 0,
    totalLatencyMs: 0,
  };

  recordCacheHit(latencyMs: number) {
    this.metrics.cacheHits++;
    this.metrics.totalQueries++;
    this.metrics.totalLatencyMs += latencyMs;
    this.logMetrics();
  }

  recordCacheMiss(latencyMs: number) {
    this.metrics.cacheMisses++;
    this.metrics.totalQueries++;
    this.metrics.totalLatencyMs += latencyMs;
    this.logMetrics();
  }

  private logMetrics() {
    if (this.metrics.totalQueries % 10 === 0) {
      // Log every 10 queries
      const hitRate =
        this.metrics.cacheHits > 0
          ? ((this.metrics.cacheHits / this.metrics.totalQueries) * 100).toFixed(1)
          : '0.0';
      const avgLatency =
        this.metrics.totalQueries > 0
          ? (this.metrics.totalLatencyMs / this.metrics.totalQueries).toFixed(0)
          : '0';

      console.error(
        `[METRICS] Queries: ${this.metrics.totalQueries} | ` +
          `Cache Hit Rate: ${hitRate}% | ` +
          `Avg Latency: ${avgLatency}ms`,
      );
    }
  }

  getMetrics() {
    return { ...this.metrics };
  }
}

export const logger = new MCPLogger();