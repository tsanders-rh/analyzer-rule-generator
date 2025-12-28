"""
Security utilities for path validation and sanitization.

Provides functions to prevent path traversal attacks and ensure
safe file operations.
"""
from pathlib import Path
from typing import Union


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
        raise ValueError(f"Cannot resolve path {path}: {e}")

    # Check if resolved path is within base directory
    # Use is_relative_to() if Python 3.9+, otherwise use manual check
    try:
        # Python 3.9+ method
        if not resolved_path.is_relative_to(resolved_base):
            raise ValueError(
                f"Path {path} resolves to {resolved_path} which is outside "
                f"base directory {base_dir} ({resolved_base})"
            )
    except AttributeError:
        # Fallback for Python < 3.9
        try:
            resolved_path.relative_to(resolved_base)
        except ValueError:
            raise ValueError(
                f"Path {path} resolves to {resolved_path} which is outside "
                f"base directory {base_dir} ({resolved_base})"
            )

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
        '../',      # Parent directory traversal
        '..\\',     # Windows parent directory traversal
        '/..',      # Absolute path parent traversal
        '\\..',     # Windows absolute path parent traversal
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
