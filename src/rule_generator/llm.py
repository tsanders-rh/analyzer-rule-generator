"""
Simple LLM adapters for rule generation.

Provides a unified interface for different LLM providers.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class LLMError(Exception):
    """Base exception for LLM provider errors."""

    pass


class LLMAPIError(LLMError):
    """API-level error (5xx, temporary failures)."""

    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded (429)."""

    pass


class LLMAuthenticationError(LLMError):
    """Authentication failed (invalid API key)."""

    pass


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate response from LLM.

        Args:
            prompt: The prompt text
            **kwargs: Provider-specific parameters

        Returns:
            Dict with 'response' key containing the generated text

        Raises:
            LLMAPIError: For API-level errors (5xx, temporary failures)
            LLMRateLimitError: For rate limit errors (429)
            LLMAuthenticationError: For authentication failures
        """
        pass

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and cleanup resources."""
        self.close()
        return False

    def close(self):
        """
        Close and cleanup resources.

        Subclasses should override this if they need cleanup.
        """
        # Default implementation: try to close the client if it has a close method
        if hasattr(self, 'client') and hasattr(self.client, 'close'):
            try:
                self.client.close()
            except Exception:
                # Ignore errors during cleanup
                pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, model: str = "gpt-4-turbo", api_key: Optional[str] = None):
        """
        Initialize OpenAI provider.

        Args:
            model: Model name (default: gpt-4-turbo)
            api_key: API key (defaults to OPENAI_API_KEY env var)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")

        self.model = model
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using OpenAI API."""
        try:
            from openai import APIError, AuthenticationError, RateLimitError
        except ImportError:
            # Fallback if exception types not available
            RateLimitError = APIError = AuthenticationError = Exception

        temperature = kwargs.get("temperature", 0.0)
        max_tokens = min(kwargs.get("max_tokens", 4096), 4096)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return {
                "response": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }
        except RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}") from e
        except AuthenticationError as e:
            raise LLMAuthenticationError(f"OpenAI authentication failed: {e}") from e
        except APIError as e:
            raise LLMAPIError(f"OpenAI API error: {e}") from e


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self, model: str = "claude-3-7-sonnet-latest", api_key: Optional[str] = None):
        """
        Initialize Anthropic provider.

        Args:
            model: Model name (default: claude-3-7-sonnet-latest)
            api_key: API key (defaults to ANTHROPIC_API_KEY env var)
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("anthropic package required. Install with: pip install anthropic")

        self.model = model
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using Anthropic API."""
        try:
            from anthropic import APIError, AuthenticationError, RateLimitError
        except ImportError:
            # Fallback if exception types not available
            RateLimitError = APIError = AuthenticationError = Exception

        temperature = kwargs.get("temperature", 0.0)
        max_tokens = kwargs.get("max_tokens", 16000)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "response": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            }
        except RateLimitError as e:
            raise LLMRateLimitError(f"Anthropic rate limit exceeded: {e}") from e
        except AuthenticationError as e:
            raise LLMAuthenticationError(f"Anthropic authentication failed: {e}") from e
        except APIError as e:
            raise LLMAPIError(f"Anthropic API error: {e}") from e


class GoogleProvider(LLMProvider):
    """Google Gemini API provider."""

    def __init__(self, model: str = "gemini-1.5-pro", api_key: Optional[str] = None):
        """
        Initialize Google provider.

        Args:
            model: Model name (default: gemini-1.5-pro)
            api_key: API key (defaults to GOOGLE_API_KEY env var)
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package required. "
                "Install with: pip install google-generativeai"
            )

        self.model_name = model
        genai.configure(api_key=api_key or os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model)

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using Google Gemini API."""
        try:
            from google.api_core.exceptions import (
                GoogleAPIError,
                ResourceExhausted,
                Unauthenticated,
            )
        except ImportError:
            # Fallback if exception types not available
            ResourceExhausted = Unauthenticated = GoogleAPIError = Exception

        temperature = kwargs.get("temperature", 0.0)

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": kwargs.get("max_tokens", 8000),
        }

        try:
            response = self.model.generate_content(prompt, generation_config=generation_config)

            return {
                "response": response.text,
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                },
            }
        except ResourceExhausted as e:
            raise LLMRateLimitError(f"Google API rate limit exceeded: {e}") from e
        except Unauthenticated as e:
            raise LLMAuthenticationError(f"Google authentication failed: {e}") from e
        except GoogleAPIError as e:
            raise LLMAPIError(f"Google API error: {e}") from e


def get_llm_provider(
    provider: str = "openai", model: Optional[str] = None, api_key: Optional[str] = None
) -> LLMProvider:
    """
    Factory function to get LLM provider.

    Args:
        provider: Provider name ('openai', 'anthropic', 'google')
        model: Model name (uses provider default if not specified)
        api_key: API key (uses environment variable if not specified)

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider is unknown
    """
    provider = provider.lower()

    if provider == "openai":
        return OpenAIProvider(model=model or "gpt-4-turbo", api_key=api_key)
    elif provider == "anthropic":
        return AnthropicProvider(model=model or "claude-3-7-sonnet-latest", api_key=api_key)
    elif provider == "google":
        return GoogleProvider(model=model or "gemini-1.5-pro", api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}. Choose from: openai, anthropic, google")
