// Error handling for Windows CLI Tool integration

export enum ErrorSeverity {
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
  FATAL = 'fatal'
}

export interface ErrorMetadata {
  command?: string;
  shell?: string;
  workingDir?: string;
  originalCommand?: string;
  severity?: ErrorSeverity;
  errorCode?: string | number;
  [key: string]: unknown;
}

export class CLIServerError extends Error {
  public readonly severity: ErrorSeverity;
  public readonly metadata: Record<string, unknown>;
  public readonly cause?: Error;

  constructor(
    message: string,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    metadata: Record<string, unknown> = {},
    cause?: Error
  ) {
    super(message);
    this.name = 'CLIServerError';
    this.severity = severity;
    this.metadata = metadata;
    this.cause = cause;
  }
}

export class CommandTimeoutError extends CLIServerError {
  constructor(command: string, timeoutMs: number) {
    super(
      `Command timed out after ${timeoutMs}ms: ${command}`,
      ErrorSeverity.ERROR,
      { command, timeoutMs }
    );
    this.name = 'CommandTimeoutError';
  }
}

export class ValidationError extends CLIServerError {
  constructor(message: string, metadata: Record<string, unknown> = {}) {
    super(message, ErrorSeverity.ERROR, metadata);
    this.name = 'ValidationError';
  }
}

export class SecurityError extends CLIServerError {
  constructor(message: string, metadata: Record<string, unknown> = {}) {
    super(message, ErrorSeverity.ERROR, metadata);
    this.name = 'SecurityError';
  }
}