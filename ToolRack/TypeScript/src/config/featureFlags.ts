interface FeatureFlags {
  ENABLE_SEMANTIC_CACHE: boolean;
  ENABLE_DEDUPLICATION: boolean;
  CACHE_TTL_SECONDS: number;
  MAX_RESULTS_PER_DOMAIN: number;
}

export const featureFlags: FeatureFlags = {
  ENABLE_SEMANTIC_CACHE: process.env.ENABLE_SEMANTIC_CACHE === 'true',
  ENABLE_DEDUPLICATION: process.env.ENABLE_DEDUPLICATION !== 'false', // Default ON
  CACHE_TTL_SECONDS: parseInt(process.env.CACHE_TTL_SECONDS || '3600'),
  MAX_RESULTS_PER_DOMAIN: parseInt(process.env.MAX_RESULTS_PER_DOMAIN || '2'),
};

export function validateFeatureFlags() {
  console.error('[Config] Feature Flags:');
  console.error(`  - Semantic Cache: ${featureFlags.ENABLE_SEMANTIC_CACHE}`);
  console.error(`  - Deduplication: ${featureFlags.ENABLE_DEDUPLICATION}`);
  console.error(`  - Cache TTL: ${featureFlags.CACHE_TTL_SECONDS}s`);
  console.error(`  - Max Results Per Domain: ${featureFlags.MAX_RESULTS_PER_DOMAIN}`);
}

