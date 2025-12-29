"""
File handling utilities for rule generator.

This module provides common file operations to reduce code duplication:
- YAML file loading with validation and error handling
- YAML file writing with consistent formatting
- Rule file parsing and normalization
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

# Set up logging
logger = logging.getLogger(__name__)


def load_yaml_file(file_path: Union[str, Path]) -> Any:
    """
    Load and parse a YAML file with comprehensive error handling.

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML data (dict or list)

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML parsing fails
        IOError: If file cannot be read

    Examples:
        >>> data = load_yaml_file("rules.yaml")
        >>> rules = data if isinstance(data, list) else [data]
    """
    path = Path(file_path)

    if not path.exists():
        logger.error(f"[FileUtils] File not found: {file_path}")
        raise FileNotFoundError("The requested file could not be found")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if data is None:
            logger.error(f"[FileUtils] Empty or invalid YAML file: {file_path}")
            raise ValueError("YAML file is empty or invalid")

        return data

    except yaml.YAMLError as e:
        logger.error(f"[FileUtils] YAML parsing error in {file_path}: {e}")
        raise yaml.YAMLError("Failed to parse YAML file")
    except IOError as e:
        logger.error(f"[FileUtils] Error reading file {file_path}: {e}")
        raise IOError("Failed to read file")


def load_rules_file(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load analyzer rules from a YAML file.

    Handles both single-rule and multi-rule formats.
    Validates that loaded data contains rule structures.

    Args:
        file_path: Path to rule YAML file

    Returns:
        List of rule dictionaries

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML parsing fails
        ValueError: If file doesn't contain valid rules

    Examples:
        >>> rules = load_rules_file("spring-boot-to-quarkus.yaml")
        >>> for rule in rules:
        ...     print(rule['ruleID'])
    """
    data = load_yaml_file(file_path)

    # Normalize to list format
    if isinstance(data, list):
        rules = data
    elif isinstance(data, dict):
        rules = [data]
    else:
        logger.error(f"[FileUtils] Invalid rule file format in {file_path}: expected list or dict")
        raise ValueError("Invalid rule file format: expected list or dict")

    # Validate that rules have required fields
    if not rules or not all(isinstance(r, dict) for r in rules):
        logger.error(
            f"[FileUtils] Invalid rule structure in {file_path}: rules must be dictionaries"
        )
        raise ValueError("Invalid rule structure: rules must be dictionaries")

    return rules


def write_yaml_file(
    file_path: Union[str, Path], data: Any, dumper: Optional[yaml.Dumper] = None, **kwargs
) -> None:
    """
    Write data to YAML file with consistent formatting.

    Args:
        file_path: Path to output YAML file
        data: Data to write (dict or list)
        dumper: Optional custom YAML dumper class
        **kwargs: Additional arguments passed to yaml.dump

    Raises:
        IOError: If file cannot be written

    Examples:
        >>> rules = [{'ruleID': 'test-00000', 'description': 'Test rule'}]
        >>> write_yaml_file("output.yaml", rules)
    """
    path = Path(file_path)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path, 'w', encoding='utf-8') as f:
            # Default kwargs for consistent formatting
            default_kwargs = {
                'default_flow_style': False,
                'sort_keys': False,
                'allow_unicode': True,
            }
            # Merge with user-provided kwargs (user kwargs take precedence)
            yaml_kwargs = {**default_kwargs, **kwargs}

            if dumper:
                yaml.dump(data, f, Dumper=dumper, **yaml_kwargs)
            else:
                yaml.dump(data, f, **yaml_kwargs)

    except IOError as e:
        logger.error(f"[FileUtils] Error writing file {file_path}: {e}")
        raise IOError("Failed to write file")


def rule_to_dict(rule: Any) -> Dict[str, Any]:
    """
    Convert an AnalyzerRule object to a dictionary for YAML serialization.

    Handles both Pydantic models and plain dictionaries.

    Args:
        rule: AnalyzerRule object or dict

    Returns:
        Rule as dictionary

    Examples:
        >>> rule_dict = rule_to_dict(analyzer_rule)
        >>> yaml.dump([rule_dict], f)
    """
    if isinstance(rule, dict):
        return rule

    # Check if it's a Pydantic model (has model_dump method)
    if hasattr(rule, 'model_dump'):
        return rule.model_dump(exclude_none=True)

    # Fallback: Manual conversion for AnalyzerRule
    return {
        'ruleID': rule.ruleID,
        'description': rule.description,
        'effort': rule.effort,
        'category': rule.category.value if hasattr(rule.category, 'value') else rule.category,
        'labels': rule.labels,
        'when': rule.when,
        'message': rule.message,
        'links': (
            [{'url': link.url, 'title': link.title} for link in rule.links] if rule.links else []
        ),
        'customVariables': (
            rule.customVariables
            if hasattr(rule, 'customVariables') and rule.customVariables
            else []
        ),
    }
