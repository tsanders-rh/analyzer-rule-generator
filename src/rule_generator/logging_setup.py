"""
Structured logging setup for analyzer rule generator.

Provides centralized logging configuration with support for:
- Debug mode with verbose output
- Performance metrics tracking
- API call logging
- Structured log formatting
- Context-aware error logging
"""

import logging
import sys
import time
from functools import wraps
from typing import Callable

from .config import config

# ANSI color codes for terminal output
COLORS = {
    'DEBUG': '\033[36m',  # Cyan
    'INFO': '\033[32m',  # Green
    'WARNING': '\033[33m',  # Yellow
    'ERROR': '\033[31m',  # Red
    'CRITICAL': '\033[35m',  # Magenta
    'RESET': '\033[0m',  # Reset
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""

    def format(self, record):
        # Add color to level name
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            levelname = record.levelname
            if levelname in COLORS:
                record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"

        return super().format(record)


def setup_logging() -> None:
    """
    Configure application-wide logging.

    Sets up handlers, formatters, and log levels based on config settings.
    Call this once at application startup.
    """
    # Determine log level
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    if config.DEBUG_MODE:
        log_level = logging.DEBUG

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)

    # Format: [2024-01-15 10:30:45] INFO [Module] Message
    if config.DEBUG_MODE:
        # More verbose format in debug mode
        formatter = ColoredFormatter(
            '[%(asctime)s] %(levelname)s [%(name)s:%(funcName)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
    else:
        # Simpler format for normal operation
        formatter = ColoredFormatter(
            '[%(asctime)s] %(levelname)s [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set third-party library log levels to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_performance(func: Callable) -> Callable:
    """
    Decorator to log function execution time.

    Only logs when config.LOG_PERFORMANCE is True.

    Usage:
        @log_performance
        def expensive_operation():
            # ...

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with performance logging
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not config.LOG_PERFORMANCE:
            return func(*args, **kwargs)

        logger = logging.getLogger(func.__module__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"Performance: {func.__name__} completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.warning(f"Performance: {func.__name__} failed after {elapsed:.2f}s: {e}")
            raise

    return wrapper


def log_api_call(provider: str, operation: str, **context) -> None:
    """
    Log an API call with structured context.

    Only logs when config.LOG_API_CALLS is True.

    Args:
        provider: API provider name (e.g., "OpenAI", "Anthropic")
        operation: Operation being performed (e.g., "generate", "embed")
        **context: Additional context to log (model, tokens, etc.)
    """
    if not config.LOG_API_CALLS:
        return

    logger = logging.getLogger('rule_generator.api')
    context_str = ', '.join(f"{k}={v}" for k, v in context.items())
    logger.debug(f"API Call: {provider}.{operation} ({context_str})")


def log_decision(logger: logging.Logger, decision: str, rationale: str, **context) -> None:
    """
    Log an important decision made by the application.

    Helps track why certain choices were made during rule generation.

    Args:
        logger: Logger instance to use
        decision: The decision that was made
        rationale: Why this decision was made
        **context: Additional context about the decision

    Example:
        log_decision(
            logger,
            "Using combo rule instead of simple nodejs.referenced",
            "Pattern requires import verification to prevent false positives",
            component="Button",
            prop="isActive"
        )
    """
    context_str = ', '.join(f"{k}={v}" for k, v in context.items()) if context else ""
    if context_str:
        logger.info(f"Decision: {decision} - {rationale} ({context_str})")
    else:
        logger.info(f"Decision: {decision} - {rationale}")


def log_error_with_context(
    logger: logging.Logger, error: Exception, operation: str, **context
) -> None:
    """
    Log an error with rich context for debugging.

    Provides structured error logging with operation context.

    Args:
        logger: Logger instance to use
        error: The exception that occurred
        operation: What operation was being performed
        **context: Additional context about the error

    Example:
        try:
            parse_yaml(file_path)
        except yaml.YAMLError as e:
            log_error_with_context(
                logger,
                e,
                "parsing YAML file",
                file_path=file_path,
                line=e.problem_mark.line if hasattr(e, 'problem_mark') else None
            )
    """
    context_str = ', '.join(f"{k}={v}" for k, v in context.items())
    logger.error(
        f"Error during {operation}: {type(error).__name__}: {error} " f"(context: {context_str})"
        if context_str
        else f"Error during {operation}: {type(error).__name__}: {error}"
    )

    # Log stack trace in debug mode
    if config.DEBUG_MODE:
        logger.debug("Stack trace:", exc_info=True)


class PerformanceTimer:
    """
    Context manager for timing code blocks.

    Usage:
        logger = get_logger(__name__)
        with PerformanceTimer(logger, "processing patterns"):
            # ... expensive operation
    """

    def __init__(self, logger: logging.Logger = None, operation: str = None):
        """
        Initialize performance timer.

        Args:
            logger: Logger to use for output (optional)
            operation: Description of the operation being timed (optional)
        """
        self.logger = logger
        self.operation = operation
        self.start_time = None
        self.end_time = None
        self.elapsed = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        if config.LOG_PERFORMANCE and self.logger and self.operation:
            self.logger.debug(f"Starting: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log result."""
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time

        if config.LOG_PERFORMANCE and self.logger and self.operation:
            if exc_type:
                self.logger.warning(f"Failed: {self.operation} after {self.elapsed:.2f}s")
            else:
                self.logger.info(f"Completed: {self.operation} in {self.elapsed:.2f}s")
