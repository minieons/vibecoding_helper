"""Anthropic (Claude) Provider 구현."""

from collections.abc import AsyncIterator
from typing import Optional

import anthropic

from vibe.core.config import get_api_key
from vibe.core.context import Message
from vibe.core.exceptions import ProviderError
from vibe.providers.base import AIProvider, Response, Usage


class AnthropicProvider(AIProvider):
    """Anthropic Claude Provider."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or get_api_key("anthropic")
        if not self._api_key:
            raise ProviderError(
                "Anthropic API 키가 설정되지 않았습니다. "
                "ANTHROPIC_API_KEY 환경변수를 설정하세요.",
                code="E010",
            )
        self._client = anthropic.AsyncAnthropic(api_key=self._api_key)

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"

    async def generate(
        self,
        messages: list[Message],
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Response:
        """응답 생성."""
        try:
            response = await self._client.messages.create(
                model=model or self.default_model,
                max_tokens=max_tokens,
                system=system or "",
                messages=[{"role": m.role, "content": m.content} for m in messages],
            )
            return Response(
                content=response.content[0].text,
                model=response.model,
                usage=Usage(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                ),
                stop_reason=response.stop_reason,
            )
        except anthropic.APIError as e:
            raise ProviderError(f"Anthropic API 오류: {e}", code="E011") from e

    async def stream(
        self,
        messages: list[Message],
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """스트리밍 응답."""
        try:
            async with self._client.messages.stream(
                model=model or self.default_model,
                max_tokens=max_tokens,
                system=system or "",
                messages=[{"role": m.role, "content": m.content} for m in messages],
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except anthropic.APIError as e:
            raise ProviderError(f"Anthropic API 오류: {e}", code="E011") from e
