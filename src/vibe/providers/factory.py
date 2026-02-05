"""Provider 팩토리."""

from typing import Literal, Optional

from vibe.core.exceptions import ProviderError
from vibe.providers.base import AIProvider

ProviderName = Literal["anthropic", "google", "openai"]


def create_provider(name: ProviderName, api_key: Optional[str] = None) -> AIProvider:
    """Provider 인스턴스 생성.

    Args:
        name: Provider 이름
        api_key: API 키 (없으면 환경변수에서 로드)

    Returns:
        AIProvider 인스턴스

    Raises:
        ProviderError: 지원하지 않는 Provider
    """
    if name == "anthropic":
        from vibe.providers.anthropic import AnthropicProvider

        return AnthropicProvider(api_key=api_key)

    elif name == "google":
        from vibe.providers.google import GoogleProvider

        return GoogleProvider(api_key=api_key)

    elif name == "openai":
        from vibe.providers.openai import OpenAIProvider

        return OpenAIProvider(api_key=api_key)

    else:
        raise ProviderError(
            f"지원하지 않는 Provider입니다: {name}. "
            "anthropic, google, openai 중 하나를 선택하세요.",
            code="E010",
        )
