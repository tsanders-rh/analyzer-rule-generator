from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider that returns predefined responses."""
    mock = Mock()
    mock.generate = Mock(
        return_value={
            "response": """[{
            "source_pattern": "javax.servlet",
            "target_pattern": "jakarta.servlet",
            "source_fqn": "javax.servlet.*",
            "location_type": "TYPE",
            "complexity": "TRIVIAL",
            "category": "api",
            "concern": "jakarta-migration",
            "rationale": "Package renamed from javax to jakarta"
        }]""",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }
    )
    return mock
