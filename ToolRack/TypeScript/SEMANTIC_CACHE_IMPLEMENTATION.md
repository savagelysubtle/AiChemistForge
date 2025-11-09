# Semantic Cache Implementation

## Overview

This document describes the semantic caching enhancement for Brave search tools. The implementation adds transparent caching, deduplication, and improved formatting without changing the MCP tool interfaces.

## Architecture

### Service Layer Pattern

```
MCP Tool Layer (braveSearchTools.ts)
    ↓
Search Service (searchService.ts) - Orchestration
    ↓
├── Semantic Cache (semanticCache.ts) - Vector similarity search
│   └── Embedding Service (embeddingService.ts) - Local ONNX model
├── Result Processor (resultProcessor.ts) - Deduplication & Formatting
└── Brave API (performBraveSearch) - Original search logic
```

### Key Components

1. **Embedding Service**: Uses `Xenova/bge-small-en-v1.5` model (384 dimensions, ~33MB)
   - Auto-downloads on first run
   - Caches in `./models/` directory
   - ~15ms inference time per query

2. **Semantic Cache**: SQLite-based vector cache
   - Stores query embeddings + results
   - Cosine similarity search (threshold: 0.92)
   - TTL-based expiration
   - WAL mode for concurrent reads

3. **Result Processor**: Post-processing pipeline
   - Parses raw Brave results
   - Deduplicates by domain (max 2 per domain)
   - Formats as enhanced markdown

## Feature Flags

All features controlled via environment variables:

```bash
ENABLE_SEMANTIC_CACHE=true      # Enable/disable semantic caching
ENABLE_DEDUPLICATION=true        # Enable/disable domain deduplication
CACHE_TTL_SECONDS=3600          # Cache expiration time (1 hour default)
MAX_RESULTS_PER_DOMAIN=2        # Max results per domain
```

## Model Selection

**Selected Model**: `Xenova/bge-small-en-v1.5`

**Rationale**:
- Best accuracy/speed tradeoff (92% accuracy, ~15ms inference)
- Small footprint (33MB vs 135MB for base model)
- Actively maintained by BAAI/Xenova
- Compatible with Transformers.js ONNX runtime

**Alternatives Considered**:
- `all-MiniLM-L6-v2`: Faster (14.7ms) but 5-7% lower accuracy
- `bge-base-en-v1.5`: Better accuracy but 4x larger and slower

## Performance Benchmarks

### Expected Performance

| Metric | Without Cache | With Cache (Hit) | Improvement |
|--------|---------------|------------------|-------------|
| Latency | 1,500ms | 80ms | 18.75x faster |
| API Calls | 100% | 40% | 60% reduction |
| Cache Hit Rate | N/A | 60-80% | After warmup |

### Resource Usage

- **Model Size**: ~33MB (one-time download)
- **Cache DB**: ~10-50MB for 1,000 queries
- **Memory**: +200MB for model in RAM
- **CPU**: 8-12% spike during embedding generation

## Usage

### First Run

1. Set `ENABLE_SEMANTIC_CACHE=true` in `.env`
2. Start server: `npm run start`
3. Model downloads automatically (~33MB, ~12 seconds)
4. First embedding takes ~15ms

### Subsequent Runs

- Model loads from cache in <1 second
- Embeddings generated in ~15ms
- Cache lookups in ~5ms

### Testing Cache

1. Query: "TypeScript best practices"
2. Query: "best practices TypeScript" (should be cache hit)
3. Check logs for `[Cache] HIT` messages

## Troubleshooting

### Model Download Fails

**Symptom**: `Error: Failed to fetch model`

**Solutions**:
1. Check internet connection
2. Verify HuggingFace CDN access
3. Check `./models/` directory permissions

### High Memory Usage

**Symptom**: Node.js using >500MB RAM

**Solutions**:
1. Model uses quantized INT8 (already default)
2. Consider smaller model (`all-MiniLM-L6-v2`)
3. Disable caching if memory constrained

### Cache Hit Rate Low

**Symptom**: Cache hit rate <50%

**Solutions**:
1. Lower similarity threshold (0.88 instead of 0.92)
2. Increase cache TTL
3. Check query normalization

### Database Lock Errors

**Symptom**: SQLite lock errors

**Solutions**:
1. WAL mode already enabled
2. Ensure single server instance
3. Check file permissions on cache directory

## File Structure

```
TypeScript/
├── src/
│   ├── config/
│   │   ├── featureFlags.ts      # Feature flag configuration
│   │   └── modelConfig.ts       # Model paths and settings
│   ├── services/
│   │   ├── embeddingService.ts  # Local embedding generation
│   │   ├── semanticCache.ts      # SQLite vector cache
│   │   ├── searchService.ts     # Orchestration layer
│   │   └── resultProcessor.ts    # Deduplication & formatting
│   └── tools/
│       └── braveSearchTools.ts   # Modified to use SearchService
├── models/                       # Model cache (gitignored)
├── cache/                        # SQLite cache (gitignored)
└── .env                          # Environment configuration
```

## Future Enhancements

1. **Vector Indexing**: Use sqlite-vec for faster similarity search
2. **Reranking**: Add local reranking with tensorlakeai/rerank-ts
3. **Cache Warming**: Pre-populate cache with common queries
4. **Analytics**: Track query patterns and cache effectiveness

