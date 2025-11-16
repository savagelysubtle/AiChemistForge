"""
Shared utilities for the unified MCP server.

This module contains essential utility functions and classes for:
- Input validation
- Security and path validation
- Exception handling
- Retry logic for tool resilience
- Basic caching (if needed)

The complex tool composition and registry systems have been removed
in favor of direct FastMCP decorators.
"""

from .exceptions import (
    ConfigurationError,
    InputValidationError,
    PathTraversalError,
    SecurityError,
    ServerError,
    ToolError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolValidationError,
    UnifiedMCPError,
    ValidationError,
    # Convenience functions
    validation_failed,
)
from .retry import (
    RetryConfig,
    RetryStrategy,
    retry_async,
    retry_on_io_error,
    retry_on_network_error,
    tool_retry,
    with_retry,
)
from .security import (
    HashUtils,
    InputSanitizer,
    PathSecurity,
    SecureRandom,
    input_sanitizer,
    # Global instances
    path_security,
    sanitize_input,
    # Convenience functions
    validate_path,
)
from .validators import (
    BooleanValidator,
    IntegerValidator,
    PathValidator,
    StringValidator,
    Validator,
    validate_boolean,
    validate_integer,
    # Convenience functions
    validate_string,
)
from .validators import (
    validate_path as validate_path_input,
)

__all__ = [
    # Exceptions
    "UnifiedMCPError",
    "ServerError",
    "ConfigurationError",
    "ToolError",
    "ToolNotFoundError",
    "ToolExecutionError",
    "ToolValidationError",
    "SecurityError",
    "PathTraversalError",
    "ValidationError",
    "InputValidationError",
    "validation_failed",
    # Retry logic
    "RetryConfig",
    "RetryStrategy",
    "with_retry",
    "tool_retry",
    "retry_on_io_error",
    "retry_on_network_error",
    "retry_async",
    # Security
    "PathSecurity",
    "InputSanitizer",
    "SecureRandom",
    "HashUtils",
    "path_security",
    "input_sanitizer",
    "validate_path",
    "sanitize_input",
    # Validators
    "Validator",
    "StringValidator",
    "IntegerValidator",
    "BooleanValidator",
    "PathValidator",
    "validate_string",
    "validate_integer",
    "validate_boolean",
    "validate_path_input",
]
