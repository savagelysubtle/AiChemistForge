import { env } from '@xenova/transformers';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Set cache directory BEFORE any model loading
const MODEL_CACHE_DIR = path.join(__dirname, '../../models');
env.cacheDir = MODEL_CACHE_DIR;

export const MODEL_CONFIG = {
  embedding: {
    model: 'Xenova/bge-small-en-v1.5',
    dimension: 384,
    cacheDir: MODEL_CACHE_DIR,
  },
  cache: {
    dbPath: './cache/search_cache.db',
    similarityThreshold: 0.92,
  },
};

console.error(`[ModelConfig] Cache directory: ${MODEL_CACHE_DIR}`);
console.error(`[ModelConfig] Embedding model: ${MODEL_CONFIG.embedding.model}`);

