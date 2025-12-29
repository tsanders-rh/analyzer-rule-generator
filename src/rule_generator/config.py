"""
Configuration constants for analyzer rule generator.

This module contains application-wide configuration values to avoid
magic numbers scattered throughout the codebase.
"""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """Application configuration constants."""

    # Logging settings
    DEBUG_MODE: bool = field(default_factory=lambda: os.getenv("DEBUG", "").lower() in ("1", "true", "yes"))
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    LOG_PERFORMANCE: bool = field(default_factory=lambda: os.getenv("LOG_PERFORMANCE", "").lower() in ("1", "true", "yes"))
    LOG_API_CALLS: bool = field(default_factory=lambda: os.getenv("LOG_API_CALLS", "").lower() in ("1", "true", "yes"))

    # Extraction settings
    EXTRACTION_CHUNK_SIZE: int = 40000  # Characters per chunk for large guides
    EXTRACTION_MAX_TOKENS: int = 8000  # Max tokens per chunk for LLM processing

    # Rule generation settings
    # Convention from https://github.com/konveyor/rulesets/blob/main/CONTRIBUTING.md
    RULE_ID_INCREMENT: int = 10  # Increment between rule IDs (Konveyor convention)
    RULE_ID_PADDING: int = 5  # Zero-padding for rule IDs (00000, 00010, etc.)

    # Validation settings
    MAX_RETRY_ATTEMPTS: int = 3  # Maximum retry attempts for API calls
    VALIDATION_BATCH_SIZE: int = 10  # Number of rules to validate in one batch

    # LLM settings
    LLM_TIMEOUT_SECONDS: int = 120  # Timeout for LLM API calls
    LLM_MAX_PATTERNS_PER_CHUNK: int = 100  # Maximum patterns to extract in one chunk

    # Test generation settings
    TEST_GENERATION_DELAY: float = 8.0  # Delay between test generation API calls
    TEST_MAX_ITERATIONS: int = 3  # Max test-fix iterations
    KANTRA_TIMEOUT_SECONDS: int = 300  # Timeout for kantra test command

    # File handling settings
    MAX_CONTENT_SIZE: int = 40000  # Max content size before chunking
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB max file size


# Global config instance
config = Config()
