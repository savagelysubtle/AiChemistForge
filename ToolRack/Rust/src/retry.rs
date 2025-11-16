/// Retry logic for tool resilience in the Rust MCP server.
///
/// This module provides retry functionality with configurable backoff strategies
/// for handling transient errors in filesystem operations.

use std::future::Future;
use std::io::ErrorKind;
use std::time::Duration;
use tokio::time::sleep;

use crate::error::ServiceError;

/// Retry strategy for backoff calculation
#[derive(Debug, Clone, Copy)]
pub enum RetryStrategy {
    /// Exponential backoff: delay doubles each retry (1s, 2s, 4s, 8s)
    Exponential,
    /// Linear backoff: delay increases linearly (1s, 2s, 3s, 4s)
    Linear,
    /// Fixed backoff: same delay for all retries (1s, 1s, 1s, 1s)
    Fixed,
}

/// Configuration for retry behavior
#[derive(Debug, Clone)]
pub struct RetryConfig {
    /// Maximum number of attempts (including initial attempt)
    pub max_attempts: u32,
    /// Initial delay in milliseconds before first retry
    pub initial_delay_ms: u64,
    /// Maximum delay in milliseconds between retries
    pub max_delay_ms: u64,
    /// Retry strategy (exponential, linear, fixed)
    pub strategy: RetryStrategy,
    /// Backoff multiplier for exponential strategy
    pub backoff_multiplier: f64,
}

impl Default for RetryConfig {
    fn default() -> Self {
        Self {
            max_attempts: 3,
            initial_delay_ms: 1000,
            max_delay_ms: 30000,
            strategy: RetryStrategy::Exponential,
            backoff_multiplier: 2.0,
        }
    }
}

impl RetryConfig {
    /// Create a new retry configuration with default values
    pub fn new() -> Self {
        Self::default()
    }

    /// Set maximum number of attempts
    pub fn with_max_attempts(mut self, max_attempts: u32) -> Self {
        self.max_attempts = max_attempts.max(1);
        self
    }

    /// Set initial delay in milliseconds
    pub fn with_initial_delay_ms(mut self, delay_ms: u64) -> Self {
        self.initial_delay_ms = delay_ms;
        self
    }

    /// Set maximum delay in milliseconds
    pub fn with_max_delay_ms(mut self, delay_ms: u64) -> Self {
        self.max_delay_ms = delay_ms.max(self.initial_delay_ms);
        self
    }

    /// Set retry strategy
    pub fn with_strategy(mut self, strategy: RetryStrategy) -> Self {
        self.strategy = strategy;
        self
    }

    /// Set backoff multiplier (for exponential strategy)
    pub fn with_backoff_multiplier(mut self, multiplier: f64) -> Self {
        self.backoff_multiplier = multiplier;
        self
    }

    /// Calculate delay for a given attempt number (0-indexed)
    pub fn calculate_delay(&self, attempt: u32) -> Duration {
        let delay_ms = match self.strategy {
            RetryStrategy::Fixed => self.initial_delay_ms,
            RetryStrategy::Linear => self.initial_delay_ms * (attempt as u64 + 1),
            RetryStrategy::Exponential => {
                let multiplier = self.backoff_multiplier.powi(attempt as i32);
                (self.initial_delay_ms as f64 * multiplier) as u64
            }
        };

        Duration::from_millis(delay_ms.min(self.max_delay_ms))
    }

    /// Check if an error is retryable
    pub fn is_retryable(&self, error: &ServiceError) -> bool {
        match error {
            // Transient I/O errors that might resolve on retry
            ServiceError::Io(io_err) => match io_err.kind() {
                ErrorKind::NotFound => false, // File doesn't exist - won't fix with retry
                ErrorKind::PermissionDenied => true, // Might be temporary lock
                ErrorKind::ConnectionRefused => true, // Network might recover
                ErrorKind::ConnectionReset => true,
                ErrorKind::ConnectionAborted => true,
                ErrorKind::NotConnected => true,
                ErrorKind::AddrInUse => true,
                ErrorKind::AddrNotAvailable => true,
                ErrorKind::BrokenPipe => true,
                ErrorKind::AlreadyExists => false, // File exists - won't fix with retry
                ErrorKind::WouldBlock => true, // Resource temporarily unavailable
                ErrorKind::InvalidInput => false, // Invalid input - won't fix with retry
                ErrorKind::InvalidData => false,
                ErrorKind::TimedOut => true, // Timeout might recover
                ErrorKind::WriteZero => true,
                ErrorKind::Interrupted => true, // Operation interrupted - retry
                ErrorKind::Unsupported => false, // Operation not supported
                ErrorKind::UnexpectedEof => false,
                ErrorKind::OutOfMemory => false, // Memory issue - likely won't fix
                ErrorKind::Other => true, // Unknown I/O error - try retry
                _ => true, // Default to retrying unknown variants
            },
            // Non-transient errors - don't retry
            ServiceError::PathNotAllowed => false, // Security violation
            ServiceError::DirectoryAlreadyExists => false, // Won't change
            ServiceError::FileNotFound(_) => false, // File doesn't exist
            ServiceError::PermissionDenied => true, // Might be temporary file lock
            ServiceError::ContentSearchError(_) => false, // Regex error - won't fix
            ServiceError::InvalidMediaFile(_) => false, // Invalid format - won't fix
        }
    }
}

/// Retry a future with configured retry behavior
///
/// # Example
///
/// ```no_run
/// use aichemistforge_mcp_server::retry::{retry_with_config, RetryConfig};
///
/// async fn my_operation() -> Result<String, ServiceError> {
///     // Your operation here
///     Ok("success".to_string())
/// }
///
/// let config = RetryConfig::default();
/// let result = retry_with_config("my_tool", || my_operation(), &config).await;
/// ```
pub async fn retry_with_config<F, Fut, T, E>(
    tool_name: &str,
    mut operation: F,
    config: &RetryConfig,
) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, E>>,
    E: std::fmt::Display + From<ServiceError>,
{
    let mut last_error: Option<E> = None;

    for attempt in 0..config.max_attempts {
        match operation().await {
            Ok(result) => {
                if attempt > 0 {
                    eprintln!(
                        "[INFO] Tool '{}' succeeded on attempt {}/{}",
                        tool_name,
                        attempt + 1,
                        config.max_attempts
                    );
                }
                return Ok(result);
            }
            Err(error) => {
                last_error = Some(error);

                // Check if we should retry
                if attempt + 1 >= config.max_attempts {
                    eprintln!(
                        "[ERROR] Tool '{}' failed after {} attempts",
                        tool_name,
                        config.max_attempts
                    );
                    break;
                }

                // Calculate delay and log retry
                let delay = config.calculate_delay(attempt);
                eprintln!(
                    "[WARN] Tool '{}' failed on attempt {}/{}: {}. Retrying in {:?}...",
                    tool_name,
                    attempt + 1,
                    config.max_attempts,
                    last_error.as_ref().unwrap(),
                    delay
                );

                // Wait before retry
                sleep(delay).await;
            }
        }
    }

    // Return last error if all retries failed
    Err(last_error.unwrap())
}

/// Retry with default configuration (3 attempts, exponential backoff)
///
/// # Example
///
/// ```no_run
/// use aichemistforge_mcp_server::retry::retry;
///
/// let result = retry("read_file", || async {
///     // Your operation here
///     Ok::<_, ServiceError>("success".to_string())
/// }).await;
/// ```
pub async fn retry<F, Fut, T, E>(tool_name: &str, operation: F) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, E>>,
    E: std::fmt::Display + From<ServiceError>,
{
    retry_with_config(tool_name, operation, &RetryConfig::default()).await
}

/// Retry specifically for I/O operations with appropriate defaults
pub async fn retry_io_operation<F, Fut, T>(tool_name: &str, operation: F) -> Result<T, ServiceError>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, ServiceError>>,
{
    let config = RetryConfig::new()
        .with_max_attempts(3)
        .with_initial_delay_ms(1000)
        .with_strategy(RetryStrategy::Exponential);

    retry_with_config(tool_name, operation, &config).await
}

/// Macro to wrap an async operation with retry logic
///
/// # Example
///
/// ```no_run
/// use aichemistforge_mcp_server::retry_async;
///
/// let result = retry_async!("read_file", 3, {
///     fs_service.read_file(path).await
/// });
/// ```
#[macro_export]
macro_rules! retry_async {
    ($tool_name:expr, $max_attempts:expr, $operation:expr) => {{
        use $crate::retry::{retry_with_config, RetryConfig};
        let config = RetryConfig::new().with_max_attempts($max_attempts);
        retry_with_config($tool_name, $operation, &config).await
    }};
}

/// Convenience function for retrying with 3 attempts
pub async fn retry_3x<F, Fut, T>(tool_name: &str, operation: F) -> Result<T, ServiceError>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, ServiceError>>,
{
    retry_io_operation(tool_name, operation).await
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{Error as IoError, ErrorKind};

    #[test]
    fn test_retry_config_defaults() {
        let config = RetryConfig::default();
        assert_eq!(config.max_attempts, 3);
        assert_eq!(config.initial_delay_ms, 1000);
        assert_eq!(config.max_delay_ms, 30000);
    }

    #[test]
    fn test_exponential_backoff() {
        let config = RetryConfig::new()
            .with_strategy(RetryStrategy::Exponential)
            .with_initial_delay_ms(1000)
            .with_backoff_multiplier(2.0);

        assert_eq!(config.calculate_delay(0), Duration::from_millis(1000));
        assert_eq!(config.calculate_delay(1), Duration::from_millis(2000));
        assert_eq!(config.calculate_delay(2), Duration::from_millis(4000));
        assert_eq!(config.calculate_delay(3), Duration::from_millis(8000));
    }

    #[test]
    fn test_linear_backoff() {
        let config = RetryConfig::new()
            .with_strategy(RetryStrategy::Linear)
            .with_initial_delay_ms(1000);

        assert_eq!(config.calculate_delay(0), Duration::from_millis(1000));
        assert_eq!(config.calculate_delay(1), Duration::from_millis(2000));
        assert_eq!(config.calculate_delay(2), Duration::from_millis(3000));
        assert_eq!(config.calculate_delay(3), Duration::from_millis(4000));
    }

    #[test]
    fn test_fixed_backoff() {
        let config = RetryConfig::new()
            .with_strategy(RetryStrategy::Fixed)
            .with_initial_delay_ms(1000);

        assert_eq!(config.calculate_delay(0), Duration::from_millis(1000));
        assert_eq!(config.calculate_delay(1), Duration::from_millis(1000));
        assert_eq!(config.calculate_delay(2), Duration::from_millis(1000));
    }

    #[test]
    fn test_max_delay_cap() {
        let config = RetryConfig::new()
            .with_strategy(RetryStrategy::Exponential)
            .with_initial_delay_ms(1000)
            .with_max_delay_ms(5000);

        assert_eq!(config.calculate_delay(10), Duration::from_millis(5000));
    }

    #[test]
    fn test_is_retryable() {
        let config = RetryConfig::default();

        // Retryable errors
        assert!(config.is_retryable(&ServiceError::Io(IoError::from(ErrorKind::PermissionDenied))));
        assert!(config.is_retryable(&ServiceError::Io(IoError::from(ErrorKind::TimedOut))));
        assert!(config.is_retryable(&ServiceError::Io(IoError::from(ErrorKind::Interrupted))));
        assert!(config.is_retryable(&ServiceError::PermissionDenied));

        // Non-retryable errors
        assert!(!config.is_retryable(&ServiceError::PathNotAllowed));
        assert!(!config.is_retryable(&ServiceError::FileNotFound("test.txt".to_string())));
        assert!(!config.is_retryable(&ServiceError::DirectoryAlreadyExists));
        assert!(!config.is_retryable(&ServiceError::Io(IoError::from(ErrorKind::NotFound))));
    }

    #[tokio::test]
    async fn test_retry_success_first_attempt() {
        let result = retry_3x("test_tool", async { Ok::<_, ServiceError>("success") }).await;
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "success");
    }

    #[tokio::test]
    async fn test_retry_success_after_failure() {
        let mut attempt = 0;
        let result = retry_3x("test_tool", async {
            attempt += 1;
            if attempt < 2 {
                Err(ServiceError::Io(IoError::from(ErrorKind::Interrupted)))
            } else {
                Ok::<_, ServiceError>("success")
            }
        })
        .await;

        assert!(result.is_ok());
    }
}


