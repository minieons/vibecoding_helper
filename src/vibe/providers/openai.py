"""OpenAI (GPT) Provider 구현."""

from collections.abc import AsyncIterator
from typing import Optional

import openai

from vibe.core.config import get_api_key
from vibe.core.context import Message
from vibe.core.exceptions import ProviderError
from vibe.providers.base import AIProvider, Response, Usage


class OpenAIProvider(AIProvider):
    """OpenAI GPT Provider."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or get_api_key("openai")
        if not self._api_key:
            raise ProviderError(
                "OpenAI API 키가 설정되지 않았습니다. "
                "OPENAI_API_KEY 환경변수를 설정하세요.",
                code="E010",
            )
        self._client = openai.AsyncOpenAI(api_key=self._api_key)

    @property
    def name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return "gpt-4o"

    def _build_messages(
        self, messages: list[Message], system: Optional[str] = None
    ) -> list[dict]:
        """메시지 목록 생성."""
        result = []
        if system:
            result.append({"role": "system", "content": system})
        for msg in messages:
            result.append({"role": msg.role, "content": msg.content})
        return result

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
            response = await self._client.chat.completions.create(
                model=model or self.default_model,
                max_tokens=max_tokens,
                messages=self._build_messages(messages, system),
            )
            choice = response.choices[0]
            return Response(
                content=choice.message.content or "",
                model=response.model,
                usage=Usage(
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                ),
                stop_reason=choice.finish_reason,
            )
        except openai.APIError as e:
            raise ProviderError(f"OpenAI API 오류: {e}", code="E011") from e

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
            stream = await self._client.chat.completions.create(
                model=model or self.default_model,
                max_tokens=max_tokens,
                messages=self._build_messages(messages, system),
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except openai.APIError as e:
            raise ProviderError(f"OpenAI API 오류: {e}", code="E011") from e
