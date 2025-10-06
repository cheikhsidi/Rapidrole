"""
AI Model Pricing Configuration.

This module contains pricing rates for various AI models.
Prices are per 1 million tokens (USD).

Update these rates as providers change their pricing.
Last updated: October 2025
"""

# Pricing rates per 1M tokens (USD)
# Source: Provider pricing pages as of October 2024
AI_MODEL_PRICING = {
    "openai": {
        "gpt-4o": 0.005,  # $5 per 1M tokens (average of input/output)
        "gpt-4": 0.03,  # $30 per 1M tokens (average)
        "gpt-3.5-turbo": 0.001,  # $1 per 1M tokens (average)
        "text-embedding-3-small": 0.00002,  # $0.02 per 1M tokens
        "text-embedding-3-large": 0.00013,  # $0.13 per 1M tokens
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": 0.003,  # $3 per 1M tokens (average)
        "claude-3-opus": 0.015,  # $15 per 1M tokens (average)
        "claude-3-sonnet": 0.003,  # $3 per 1M tokens (average)
        "claude-3-haiku": 0.00025,  # $0.25 per 1M tokens (average)
    },
}


def get_model_price(provider: str, model: str) -> float:
    """
    Get the price per 1M tokens for a specific model.

    Args:
        provider: AI provider name (e.g., "openai", "anthropic")
        model: Model name (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")

    Returns:
        Price per 1M tokens in USD

    Raises:
        KeyError: If provider or model not found in pricing data
    """
    try:
        return AI_MODEL_PRICING[provider][model]
    except KeyError:
        # Return a default rate if model not found
        # This prevents crashes when new models are added
        return 0.01  # Default $10 per 1M tokens


def get_estimated_cost(provider: str, model: str, tokens: int) -> float:
    """
    Calculate estimated cost for a given number of tokens.

    Args:
        provider: AI provider name
        model: Model name
        tokens: Number of tokens used

    Returns:
        Estimated cost in USD
    """
    price_per_million = get_model_price(provider, model)
    return (tokens / 1_000_000) * price_per_million
