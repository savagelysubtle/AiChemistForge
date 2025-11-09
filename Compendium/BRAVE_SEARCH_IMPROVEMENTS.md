# Brave Search Tools - Rate Limiting and Retry Improvements

## Overview
Enhanced the Brave Search tools with intelligent retry logic, exponential backoff, and proper rate limit tracking to prevent wasted tool calls and respect Brave's free tier API limits.

## Key Improvements

### 1. **Accurate Rate Limit Tracking**
- **Per-second limit**: 1 request/second (was incorrectly set to 15,000/month)
- **Monthly limit**: 2,000 requests/month (corrected from 15,000)
- Separate tracking for per-second and monthly counters with proper reset timers
- Monthly counter resets after 30 days (2,592,000,000 ms)

### 2. **Exponential Backoff with Jitter**
```typescript
const RETRY_CONFIG = {
  maxAttempts: 3,           // Maximum 3 retry attempts
  initialDelayMs: 1000,     // Start with 1 second delay
  maxDelayMs: 10000,        // Cap at 10 seconds
  backoffMultiplier: 2,     // Doubles delay each retry
  jitterFactor: 0.1         // 10% random jitter to avoid thundering herd
};
```

**Benefits:**
- Prevents thundering herd problem with random jitter
- Doubles wait time between retries (1s → 2s → 4s)
- Caps maximum wait at 10 seconds
- Respects `Retry-After` header when provided by API

### 3. **Intelligent Rate Limit Handling**

#### Pre-flight Checks
- Validates rate limits **before** making API calls
- Checks monthly limit first (hard limit - cannot retry)
- Checks per-second limit (soft limit - can wait and retry)
- Returns detailed error messages with time until reset

#### Response-based Retries
- Detects 429 (Too Many Requests) responses from API
- Extracts `Retry-After` header when available
- Applies exponential backoff if header not present
- Logs retry attempts to stderr for debugging

### 4. **Error Handling Improvements**

#### Timeout Handling
- 10-second timeout per request (unchanged)
- Detects `AbortError` and retries with backoff
- Increments retry counter only on retryable errors

#### Non-retryable Errors
- Network errors, 4xx errors (except 429), 5xx errors throw immediately
- Saves API quota by not retrying permanent failures
- Provides clear error messages to users

### 5. **Multi-Link Search Optimization**

**Changed from concurrent to sequential execution:**
```typescript
// OLD: All queries executed concurrently (triggers rate limits)
const searchPromises = queries.map(query => performSearch(query));
await Promise.all(searchPromises);

// NEW: Sequential execution with delays
for (let i = 0; i < queries.length; i++) {
  const results = await performSearch(queries[i]);
  if (i < queries.length - 1) {
    await sleep(1100); // 1.1s delay between queries
  }
}
```

**Benefits:**
- Respects 1 req/sec limit by adding 1.1s delay between queries
- Allows first query to complete before starting next
- Provides progress logging for long multi-query searches
- Still completes all queries, just sequentially

### 6. **Consolidated Retry Logic**
- All search functions (`performBraveSearch`, `performBraveSearchForQuery`) use same retry mechanism
- `performBraveSearchForQuery` delegates to main function instead of duplicating code
- Consistent error handling across all search types (web, code, multi-link)

## Rate Limit Counter Details

### Per-Second Counter
```typescript
if (now - requestCount.lastSecondReset >= 1000) {
  requestCount.second = 0;  // Reset after 1 second
  requestCount.lastSecondReset = now;
}
```

### Monthly Counter
```typescript
if (now - requestCount.lastMonthReset >= 2592000000) {  // 30 days
  requestCount.month = 0;
  requestCount.lastMonthReset = now;
}
```

### Counter Incrementation
- **Only increments after successful API response** (status 200)
- Failed requests don't count toward quota
- Prevents counting retried requests multiple times

## Error Messages

### Rate Limit Exceeded (Monthly)
```
Monthly rate limit of 2000 requests exceeded. Resets in X days.
```

### Rate Limit Exceeded (Per-Second)
```
Per-second rate limit reached. Wait Xms before retry.
[Brave Search] Waiting 1123ms before retry 2/3...
```

### 429 Response from API
```
Brave API rate limit exceeded (429). Attempt 2/3
[Brave Search] Waiting 2045ms before retry...
```

### Timeout
```
Request timeout after 10 seconds. Attempt 1/3
[Brave Search] Waiting 981ms before retry...
```

## Testing Recommendations

### 1. Test Rate Limit Behavior
```typescript
// Make rapid requests to trigger per-second limit
for (let i = 0; i < 5; i++) {
  await executeWebSearch({ query: "test" });
}
// Should see retry messages with ~1s delays
```

### 2. Test Monthly Limit
```typescript
// Simulate monthly limit reached
requestCount.month = 2000;
await executeWebSearch({ query: "test" });
// Should fail immediately with monthly limit message
```

### 3. Test Multi-Link Search
```typescript
await executeMultiLinkSearch({
  queries: ["query1", "query2", "query3"],
  count: 5
});
// Should execute sequentially with 1.1s delays
// Check stderr logs for progress updates
```

### 4. Test Exponential Backoff
```typescript
// Mock API to return 429 responses
// Verify delays increase: ~1s, ~2s, ~4s
// Verify jitter is applied (delays slightly vary)
```

## Migration Notes

### Breaking Changes
- **None** - All changes are backward compatible
- Existing tool calls work identically from user perspective

### Behavioral Changes
1. **Multi-link search is slower** (but respects rate limits)
   - 3 queries now takes ~3.3 seconds instead of instant
   - Progress logged to stderr

2. **Failed requests may take longer** (due to retries)
   - Up to 3 attempts with exponential backoff
   - Maximum ~15 seconds for complete failure (3 attempts × ~5s avg)

3. **Better quota management**
   - Only successful requests count toward quota
   - Retries don't waste monthly allowance

## Performance Impact

### Before Improvements
- Concurrent requests → Instant rate limit errors
- No retries → Wasted tool calls
- Poor monthly tracking → Unexpected quota exhaustion

### After Improvements
- Sequential + retry → Reliable execution
- Smart retries → No wasted tool calls
- Accurate tracking → Predictable quota usage

### Latency Comparison
| Scenario | Before | After |
|----------|--------|-------|
| Single query (success) | ~500ms | ~500ms ✅ |
| Single query (rate limited) | Error | ~1.5s (retry) ✅ |
| 3-query multi-search (success) | ~500ms | ~3.3s ⚠️ |
| 3-query multi-search (rate limited) | Multiple errors | ~5s (retries) ✅ |

## Configuration

### Tuning Retry Behavior
Edit `RETRY_CONFIG` to adjust retry behavior:

```typescript
// More aggressive retries (faster but more API calls)
const RETRY_CONFIG = {
  maxAttempts: 5,
  initialDelayMs: 500,
  maxDelayMs: 5000,
  backoffMultiplier: 1.5,
  jitterFactor: 0.05
};

// Conservative retries (slower but gentler on API)
const RETRY_CONFIG = {
  maxAttempts: 2,
  initialDelayMs: 2000,
  maxDelayMs: 15000,
  backoffMultiplier: 3,
  jitterFactor: 0.2
};
```

### Adjusting Rate Limits
If you upgrade to paid tier, update limits:

```typescript
const RATE_LIMIT = {
  perSecond: 20,      // Paid tier: 20 req/sec
  perMonth: 20000000  // Paid tier: 20M req/month
};
```

## Monitoring and Debugging

### Enable Debug Logging
All retry logic logs to `stderr`:
```
[Brave Search] Rate limit check failed on attempt 1. Per-second rate limit reached. Wait 234ms before retry.
[Brave Search] Waiting 256ms before retry 2/3...
[Multi-Link Search] Processing 3 queries sequentially to respect rate limits...
[Multi-Link Search] Query 1/3: "example query"
```

### Check Rate Limit Status
```typescript
// View current rate limit counters (for debugging)
console.error('Current usage:', {
  second: requestCount.second,
  month: requestCount.month,
  lastSecondReset: new Date(requestCount.lastSecondReset),
  lastMonthReset: new Date(requestCount.lastMonthReset)
});
```

## Future Enhancements

### Potential Improvements
1. **Persistent counter storage** - Track monthly usage across server restarts
2. **Quota warning system** - Alert when approaching monthly limit (e.g., 90% used)
3. **Dynamic backoff** - Adjust retry behavior based on historical success rates
4. **Request queuing** - Queue requests when rate limited instead of failing
5. **Circuit breaker** - Temporarily disable API calls after repeated failures

### Performance Optimizations
1. **Batch similar queries** - Combine similar searches into single query with OR operators
2. **Result caching** - Cache recent search results (with TTL)
3. **Adaptive rate limiting** - Learn optimal request rate from API responses

---

## Summary

These improvements ensure the Brave Search tools are:
- ✅ **Reliable** - Automatic retries handle transient failures
- ✅ **Efficient** - Smart backoff prevents wasted API quota
- ✅ **Respectful** - Honors API rate limits and terms of service
- ✅ **Observable** - Clear logging for debugging and monitoring
- ✅ **Maintainable** - Consolidated retry logic, easy to update

The tools now provide a production-ready experience for AI agents, preventing wasted tool calls and ensuring consistent availability within Brave's free tier constraints.


