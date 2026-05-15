from providers.openai import OpenAIProvider
from providers.anthropic import AnthropicProvider
from providers.gemini import GeminiProvider
from providers.openrouter import OpenRouterProvider
from providers.deepseek import DeepSeekProvider
from providers.base import BaseProvider

REGISTRY: dict[str, type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "openrouter": OpenRouterProvider,
    "deepseek": DeepSeekProvider,
}


def get_adapter(name: str, api_key: str, api_url: str) -> BaseProvider:
    cls = REGISTRY.get(name.lower())
    if cls is None:
        raise ValueError(f"No adapter registered for provider '{name}'. "
                         f"Known providers: {', '.join(REGISTRY)}")
    return cls(api_key=api_key, api_url=api_url)
