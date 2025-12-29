"""
Security utilities for path validation and sanitization.

Provides functions to prevent path traversal attacks and ensure
safe file operations, plus input validation utilities.
"""

import logging
import re
from pathlib import Path
from typing import Literal, Union

# Set up logging
logger = logging.getLogger(__name__)

# Valid complexity values
VALID_COMPLEXITIES = Literal["TRIVIAL", "LOW", "MEDIUM", "HIGH", "EXPERT"]
COMPLEXITY_VALUES = ["TRIVIAL", "LOW", "MEDIUM", "HIGH", "EXPERT"]

# Compiled regex patterns for performance (used in validation functions)
FRAMEWORK_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\-._]+$')
RULE_ID_PATTERN = re.compile(r'^[a-z0-9\-]+-\d{5}$', re.IGNORECASE)


def validate_path(path: Union[str, Path], base_dir: Union[str, Path]) -> Path:
    """
    Validate that a path is within the base directory and resolve symlinks.

    This prevents path traversal attacks by ensuring the resolved path
    is a subdirectory of the base directory.

    Args:
        path: Path to validate (can be relative or absolute)
        base_dir: Base directory that path must be within

    Returns:
        Resolved absolute path

    Raises:
        ValueError: If path is outside base_dir or contains suspicious patterns

    Examples:
        >>> validate_path("output/rules.yaml", "/safe/base")  # OK
        Path('/safe/base/output/rules.yaml')

        >>> validate_path("../../../etc/passwd", "/safe/base")  # ERROR
        ValueError: Path is outside base directory
    """
    path_obj = Path(path)
    base_obj = Path(base_dir)

    # Resolve both paths to absolute paths and follow symlinks
    try:
        resolved_path = path_obj.resolve()
        resolved_base = base_obj.resolve()
    except (OSError, RuntimeError) as e:
        logger.error(f"[Security] Cannot resolve path {path}: {e}")
        raise ValueError("Invalid or inaccessible path")

    # Check if resolved path is within base directory
    # Use is_relative_to() if Python 3.9+, otherwise use manual check
    try:
        # Python 3.9+ method
        if not resolved_path.is_relative_to(resolved_base):
            logger.error(
                f"[Security] Path traversal attempt: {path} resolves to {resolved_path} "
                f"which is outside base directory {base_dir} ({resolved_base})"
            )
            raise ValueError("Path is outside allowed directory")
    except AttributeError:
        # Fallback for Python < 3.9
        try:
            resolved_path.relative_to(resolved_base)
        except ValueError:
            logger.error(
                f"[Security] Path traversal attempt: {path} resolves to {resolved_path} "
                f"which is outside base directory {base_dir} ({resolved_base})"
            )
            raise ValueError("Path is outside allowed directory")

    return resolved_path


def sanitize_filename(filename: str, allow_path: bool = False) -> str:
    """
    Sanitize a filename to remove potentially dangerous characters.

    Args:
        filename: Filename to sanitize
        allow_path: If True, allow path separators (/ and \\)

    Returns:
        Sanitized filename

    Raises:
        ValueError: If filename is empty after sanitization

    Examples:
        >>> sanitize_filename("my-file.yaml")
        'my-file.yaml'

        >>> sanitize_filename("../../../etc/passwd")
        'etcpasswd'

        >>> sanitize_filename("output/rules.yaml", allow_path=True)
        'output/rules.yaml'
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    # Remove null bytes
    sanitized = filename.replace('\x00', '')

    if not allow_path:
        # Remove path separators and parent directory references
        sanitized = sanitized.replace('/', '').replace('\\', '')
        sanitized = sanitized.replace('..', '')

    # Remove other potentially dangerous characters
    dangerous_chars = ['|', '<', '>', ':', '"', '?', '*', '\n', '\r']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')

    if not sanitized:
        raise ValueError(f"Filename '{filename}' is invalid after sanitization")

    return sanitized


def is_safe_path(path: Union[str, Path]) -> bool:
    """
    Check if a path appears safe (quick heuristic check).

    This is a lightweight check for obviously suspicious paths.
    For full validation, use validate_path().

    Args:
        path: Path to check

    Returns:
        True if path appears safe, False otherwise

    Examples:
        >>> is_safe_path("output/rules.yaml")
        True

        >>> is_safe_path("../../../etc/passwd")
        False

        >>> is_safe_path("/absolute/path")
        True

        >>> is_safe_path("path/with/null\x00byte")
        False
    """
    path_str = str(path)

    # Check for null bytes
    if '\x00' in path_str:
        return False

    # Check for suspicious patterns
    suspicious_patterns = [
        '../',  # Parent directory traversal
        '..\\',  # Windows parent directory traversal
        '/..',  # Absolute path parent traversal
        '\\..',  # Windows absolute path parent traversal
    ]

    for pattern in suspicious_patterns:
        if pattern in path_str:
            return False

    # Check for absolute paths to sensitive directories (Unix)
    sensitive_dirs = ['/etc', '/root', '/var', '/proc', '/sys']
    path_lower = path_str.lower()
    for sens_dir in sensitive_dirs:
        if path_lower.startswith(sens_dir):
            return False

    return True


def validate_framework_name(name: str) -> str:
    """
    Validate and normalize framework name.

    Args:
        name: Framework name to validate

    Returns:
        Normalized framework name

    Raises:
        ValueError: If framework name is invalid

    Examples:
        >>> validate_framework_name("spring-boot-3.0")
        'spring-boot-3.0'

        >>> validate_framework_name("")
        ValueError: Framework name cannot be empty
    """
    if not name or not name.strip():
        raise ValueError("Framework name cannot be empty")

    name = name.strip()

    if len(name) > 100:
        raise ValueError(f"Framework name too long (max 100 chars): {name}")

    # Allow only alphanumeric, hyphens, dots, underscores
    if not FRAMEWORK_NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid framework name '{name}': "
            f"only alphanumeric characters, hyphens, dots, and underscores allowed"
        )

    return name


def validate_complexity(complexity: str) -> str:
    """
    Validate complexity value.

    Args:
        complexity: Complexity value to validate

    Returns:
        Normalized complexity value (uppercase)

    Raises:
        ValueError: If complexity is not valid

    Examples:
        >>> validate_complexity("low")
        'LOW'

        >>> validate_complexity("invalid")
        ValueError: Invalid complexity
    """
    if not complexity:
        raise ValueError("Complexity cannot be empty")

    normalized = complexity.upper().strip()

    if normalized not in COMPLEXITY_VALUES:
        raise ValueError(
            f"Invalid complexity: {complexity}. " f"Must be one of: {', '.join(COMPLEXITY_VALUES)}"
        )

    return normalized


def validate_rule_id(rule_id: str, source: str = None, target: str = None) -> str:
    """
    Validate rule ID format.

    Rule IDs should follow Konveyor convention:
    - Format: {prefix}-{number}
    - Number should be 5 digits (00000-99999)
    - Prefix typically includes source and target frameworks

    Args:
        rule_id: Rule ID to validate
        source: Optional source framework name
        target: Optional target framework name

    Returns:
        Validated rule ID

    Raises:
        ValueError: If rule ID format is invalid

    Examples:
        >>> validate_rule_id("spring-boot-to-quarkus-00010")
        'spring-boot-to-quarkus-00010'

        >>> validate_rule_id("invalid")
        ValueError: Invalid rule ID format
    """
    if not rule_id or not rule_id.strip():
        raise ValueError("Rule ID cannot be empty")

    rule_id = rule_id.strip()

    # Check basic format: {prefix}-{number}
    if not RULE_ID_PATTERN.match(rule_id):
        raise ValueError(
            f"Invalid rule ID format: {rule_id}. " f"Expected format: prefix-00000 (5-digit number)"
        )

    # If source/target provided, verify they're in the rule ID
    if source and target:
        expected_prefix = f"{source}-to-{target}"
        if not rule_id.lower().startswith(expected_prefix.lower()):
            raise ValueError(
                f"Rule ID '{rule_id}' does not match expected prefix '{expected_prefix}'"
            )

    return rule_id


def validate_llm_response(response: str, expected_format: str = "json_array") -> str:
    """
    Validate LLM response structure before parsing.

    Args:
        response: LLM response text
        expected_format: Expected response format ("json_array", "json_object", "yaml")

    Returns:
        Validated response text

    Raises:
        ValueError: If response structure is invalid

    Examples:
        >>> validate_llm_response('[{"key": "value"}]', "json_array")
        '[{"key": "value"}]'

        >>> validate_llm_response('invalid', "json_array")
        ValueError: Invalid LLM response
    """
    if not response or not response.strip():
        raise ValueError("LLM response cannot be empty")

    response = response.strip()

    # Check for minimum length (avoid trivial responses)
    if len(response) < 2:
        raise ValueError(f"LLM response too short: {len(response)} chars (expected at least 2)")

    # Validate based on expected format
    if expected_format == "json_array":
        if not response.startswith('['):
            raise ValueError(
                f"LLM response does not start with '[' (expected JSON array): "
                f"{response[:50]}..."
            )
        if not response.rstrip().endswith(']'):
            raise ValueError(
                f"LLM response does not end with ']' (expected JSON array): "
                f"...{response[-50:]}"
            )

    elif expected_format == "json_object":
        if not response.startswith('{'):
            raise ValueError(
                f"LLM response does not start with '{{' (expected JSON object): "
                f"{response[:50]}..."
            )
        if not response.rstrip().endswith('}'):
            raise ValueError(
                f"LLM response does not end with '}}' (expected JSON object): "
                f"...{response[-50:]}"
            )

    elif expected_format == "yaml":
        # Basic YAML validation - should not be pure JSON
        if response.startswith(('[', '{')):
            raise ValueError(
                f"LLM response looks like JSON, expected YAML: {response[:50]}..."
            )

    return response
