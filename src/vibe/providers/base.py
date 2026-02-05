"""AI Provider 추상 클래스."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Optional

from pydantic import BaseModel

from vibe.core.context import Message


class Usage(BaseModel):
    """토큰 사용량."""

    input_tokens: int
    output_tokens: int


class Response(BaseModel):
    """AI 응답."""

    content: str
    model: str
    usage: Usage
    stop_reason: Optional[str] = None


class AIProvider(ABC):
    """AI Provider 추상 기반 클래스."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 이름."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """기본 모델."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Response:
        """응답 생성."""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """스트리밍 응답."""
        pass
