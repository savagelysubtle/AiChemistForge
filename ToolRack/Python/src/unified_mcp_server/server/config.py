"""Server configuration management for the unified MCP server.

Enhanced with performance tuning, monitoring, and middleware settings.
"""

import os
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ServerConfig(BaseModel):
    """Configuration for the unified MCP server."""

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    # Server Settings
    server_name: str = Field(
        default="aichemistforge-mcp-server", description="MCP server name"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    transport_type: str = Field(
        default="stdio", description="Transport type (stdio or sse)"
    )

    # Database Settings
    cursor_path: Optional[str] = Field(
        default=None, description="Path to Cursor IDE directory"
    )
    project_directories: List[str] = Field(
        default_factory=list, description="Additional project directories"
    )

    # File System Settings
    allowed_paths: List[str] = Field(
        default_factory=list, description="Allowed file system paths"
    )
    max_file_size: int = Field(
        default=10_000_000, description="Maximum file size in bytes"
    )

    # Security Settings
    enable_path_traversal_check: bool = Field(
        default=True, description="Enable path traversal protection"
    )
    max_query_results: int = Field(default=1000, description="Maximum query results")

    # Performance Tuning Settings
    operation_timeout: float = Field(
        default=30.0, description="Default timeout for operations (seconds)"
    )
    retry_max_attempts: int = Field(
        default=3, description="Maximum retry attempts for failed operations"
    )
    retry_initial_delay: float = Field(
        default=1.0, description="Initial delay between retries (seconds)"
    )
    retry_max_delay: float = Field(
        default=60.0, description="Maximum delay between retries (seconds)"
    )
    max_concurrent_operations: int = Field(
        default=10, description="Maximum concurrent operations"
    )
    cache_max_size: int = Field(
        default=1000, description="Maximum cache size (entries)"
    )
    cache_default_ttl: float = Field(
        default=300.0, description="Default cache TTL (seconds)"
    )

    # Monitoring Settings
    metrics_enabled: bool = Field(
        default=True, description="Enable metrics collection"
    )
    tracing_enabled: bool = Field(
        default=True, description="Enable request tracing"
    )
    health_check_enabled: bool = Field(
        default=True, description="Enable health check endpoint"
    )

    # Middleware Settings
    rate_limit_enabled: bool = Field(
        default=False, description="Enable rate limiting"
    )
    rate_limit_max_requests: int = Field(
        default=100, description="Maximum requests per window"
    )
    rate_limit_window_seconds: float = Field(
        default=60.0, description="Rate limit window (seconds)"
    )
    rate_limit_per_tool: bool = Field(
        default=False, description="Apply rate limit per tool (vs global)"
    )
    validation_enabled: bool = Field(
        default=True, description="Enable request validation"
    )

    @field_validator("project_directories", mode="before")
    @classmethod
    def parse_project_directories(cls, v):
        """Parse project directories from string or list."""
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    @field_validator("allowed_paths", mode="before")
    @classmethod
    def parse_allowed_paths(cls, v):
        """Parse allowed paths from string or list."""
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v


def load_config() -> ServerConfig:
    """Load configuration from environment variables and .env file."""
    # Read environment variables
    config_data = {}

    # Map environment variables to config fields
    env_mapping = {
        "MCP_SERVER_NAME": "server_name",
        "MCP_LOG_LEVEL": "log_level",
        "MCP_TRANSPORT_TYPE": "transport_type",
        "CURSOR_PATH": "cursor_path",
        "PROJECT_DIRS": "project_directories",
        "ALLOWED_PATHS": "allowed_paths",
        "MAX_FILE_SIZE": "max_file_size",
        "ENABLE_PATH_TRAVERSAL_CHECK": "enable_path_traversal_check",
        "MAX_QUERY_RESULTS": "max_query_results",
        # Performance tuning
        "OPERATION_TIMEOUT": "operation_timeout",
        "RETRY_MAX_ATTEMPTS": "retry_max_attempts",
        "RETRY_INITIAL_DELAY": "retry_initial_delay",
        "RETRY_MAX_DELAY": "retry_max_delay",
        "MAX_CONCURRENT_OPERATIONS": "max_concurrent_operations",
        "CACHE_MAX_SIZE": "cache_max_size",
        "CACHE_DEFAULT_TTL": "cache_default_ttl",
        # Monitoring
        "METRICS_ENABLED": "metrics_enabled",
        "TRACING_ENABLED": "tracing_enabled",
        "HEALTH_CHECK_ENABLED": "health_check_enabled",
        # Middleware
        "RATE_LIMIT_ENABLED": "rate_limit_enabled",
        "RATE_LIMIT_MAX_REQUESTS": "rate_limit_max_requests",
        "RATE_LIMIT_WINDOW_SECONDS": "rate_limit_window_seconds",
        "RATE_LIMIT_PER_TOOL": "rate_limit_per_tool",
        "VALIDATION_ENABLED": "validation_enabled",
    }

    for env_var, field_name in env_mapping.items():
        value = os.getenv(env_var)
        if value is not None:
            # Convert string values to appropriate types
            if field_name in [
                "max_file_size",
                "max_query_results",
                "retry_max_attempts",
                "max_concurrent_operations",
                "cache_max_size",
                "rate_limit_max_requests",
            ]:
                try:
                    config_data[field_name] = int(value)
                except ValueError:
                    pass
            elif field_name in [
                "operation_timeout",
                "retry_initial_delay",
                "retry_max_delay",
                "cache_default_ttl",
                "rate_limit_window_seconds",
            ]:
                try:
                    config_data[field_name] = float(value)
                except ValueError:
                    pass
            elif field_name in [
                "enable_path_traversal_check",
                "metrics_enabled",
                "tracing_enabled",
                "health_check_enabled",
                "rate_limit_enabled",
                "rate_limit_per_tool",
                "validation_enabled",
            ]:
                config_data[field_name] = value.lower() in ("true", "1", "yes", "on")
            else:
                config_data[field_name] = value

    return ServerConfig(**config_data)


# Global config instance
config = load_config()
