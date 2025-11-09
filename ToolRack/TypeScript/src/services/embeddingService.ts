import { pipeline, env } from '@xenova/transformers';
import { MODEL_CONFIG } from '../config/modelConfig.js';
import { log } from '../utils/logger.js';

class EmbeddingService {
  private static pipeline: any = null;
  private static initialized = false;
  private static readonly MODEL = MODEL_CONFIG.embedding.model;
  private static readonly DIMENSION = MODEL_CONFIG.embedding.dimension;

  /**
   * Initialize the embedding model (async, called once on server startup)
   */
  static async initialize(): Promise<void> {
    if (this.initialized) return;

    log('info', '[Embeddings] Initializing model...');
    log('info', `[Embeddings] Cache directory: ${env.cacheDir}`);
    log('info', `[Embeddings] Model: ${this.MODEL}`);

    const startTime = Date.now();

    try {
      this.pipeline = await pipeline('feature-extraction', this.MODEL, {
        quantized: true, // Use INT8 quantization for 2-3x speedup
      });

      this.initialized = true;
      const loadTime = Date.now() - startTime;

      log('info', `[Embeddings] Model loaded in ${loadTime}ms`);
      log('info', `[Embeddings] Model dimension: ${this.DIMENSION}`);

      // First call is always slower due to WASM initialization
      // Do a warmup embedding
      await this.embed('warmup query');
      log('info', '[Embeddings] Warmup complete');
    } catch (error) {
      log('error', '[Embeddings] Failed to load model', { error });
      throw error;
    }
  }

  /**
   * Generate embedding for a query string
   * @param text - Input text to embed
   * @returns Float32Array of embeddings
   */
  static async embed(text: string): Promise<Float32Array> {
    if (!this.initialized) {
      await this.initialize();
    }

    const startTime = Date.now();

    try {
      const output = await this.pipeline(text, {
        pooling: 'mean',
        normalize: true,
      });

      const embedTime = Date.now() - startTime;

      if (text !== 'warmup query') {
        log('info', `[Embeddings] Generated embedding in ${embedTime}ms`);
      }

      // Extract Float32Array from tensor
      return output.data as Float32Array;
    } catch (error) {
      log('error', '[Embeddings] Failed to generate embedding', { error });
      throw error;
    }
  }

  /**
   * Get model metadata
   */
  static getInfo() {
    return {
      model: this.MODEL,
      dimension: this.DIMENSION,
      initialized: this.initialized,
      cacheDir: env.cacheDir,
    };
  }
}

export const embeddings = EmbeddingService;

/**
 * Calculate cosine similarity between two vectors
 */
export function cosineSimilarity(
  vecA: Float32Array,
  vecB: Float32Array,
): number {
  if (vecA.length !== vecB.length) {
    throw new Error(
      `Vector dimension mismatch: ${vecA.length} vs ${vecB.length}`,
    );
  }

  let dotProduct = 0;
  let magnitudeA = 0;
  let magnitudeB = 0;

  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    magnitudeA += vecA[i] * vecA[i];
    magnitudeB += vecB[i] * vecB[i];
  }

  magnitudeA = Math.sqrt(magnitudeA);
  magnitudeB = Math.sqrt(magnitudeB);

  if (magnitudeA === 0 || magnitudeB === 0) {
    return 0;
  }

  return dotProduct / (magnitudeA * magnitudeB);
}

