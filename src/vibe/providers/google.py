"""Google (Gemini) Provider 구현."""

from collections.abc import AsyncIterator
from typing import Optional

import google.generativeai as genai

from vibe.core.config import get_api_key
from vibe.core.context import Message
from vibe.core.exceptions import ProviderError
from vibe.providers.base import AIProvider, Response, Usage


class GoogleProvider(AIProvider):
    """Google Gemini Provider."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or get_api_key("google")
        if not self._api_key:
            raise ProviderError(
                "Google API 키가 설정되지 않았습니다. "
                "GOOGLE_API_KEY 환경변수를 설정하세요.",
                code="E010",
            )
        genai.configure(api_key=self._api_key)

    @property
    def name(self) -> str:
        return "google"

    @property
    def default_model(self) -> str:
        return "gemini-1.5-pro"

    def _convert_messages(
        self, messages: list[Message], system: Optional[str] = None
    ) -> tuple[Optional[str], list[dict]]:
        """메시지를 Gemini 형식으로 변환."""
        history = []
        for msg in messages:
            role = "model" if msg.role == "assistant" else "user"
            history.append({"role": role, "parts": [msg.content]})
        return system, history

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
            model_instance = genai.GenerativeModel(
                model_name=model or self.default_model,
                system_instruction=system,
            )
            _, history = self._convert_messages(messages)
            chat = model_instance.start_chat(history=history[:-1] if history else [])

            last_message = history[-1]["parts"][0] if history else ""
            response = await chat.send_message_async(
                last_message,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                ),
            )

            return Response(
                content=response.text,
                model=model or self.default_model,
                usage=Usage(
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.candidates_token_count,
                ),
            )
        except Exception as e:
            raise ProviderError(f"Google API 오류: {e}", code="E011") from e

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
            model_instance = genai.GenerativeModel(
                model_name=model or self.default_model,
                system_instruction=system,
            )
            _, history = self._convert_messages(messages)
            chat = model_instance.start_chat(history=history[:-1] if history else [])

            last_message = history[-1]["parts"][0] if history else ""
            response = await chat.send_message_async(
                last_message,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                ),
                stream=True,
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise ProviderError(f"Google API 오류: {e}", code="E011") from e
