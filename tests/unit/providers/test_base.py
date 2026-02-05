"""Provider base 모듈 테스트."""

from collections.abc import AsyncIterator
from typing import Optional

import pytest

from vibe.core.context import Message
from vibe.providers.base import AIProvider, Response, Usage


class TestUsage:
    """Usage 모델 테스트."""

    def test_create(self):
        """생성 테스트."""
        usage = Usage(input_tokens=100, output_tokens=200)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 200

    def test_total_tokens(self):
        """총 토큰 수."""
        usage = Usage(input_tokens=150, output_tokens=350)
        total = usage.input_tokens + usage.output_tokens
        assert total == 500


class TestResponse:
    """Response 모델 테스트."""

    def test_create(self):
        """생성 테스트."""
        response = Response(
            content="Hello, world!",
            model="claude-3-sonnet",
            usage=Usage(input_tokens=10, output_tokens=20),
            stop_reason="end_turn",
        )
        assert response.content == "Hello, world!"
        assert response.model == "claude-3-sonnet"
        assert response.usage.input_tokens == 10
        assert response.stop_reason == "end_turn"

    def test_defaults(self):
        """기본값 테스트."""
        response = Response(
            content="Test",
            model="test-model",
            usage=Usage(input_tokens=1, output_tokens=1),
        )
        assert response.stop_reason is None


class MockProvider(AIProvider):
    """테스트용 Mock Provider."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return "mock-model-v1"

    async def generate(
        self,
        messages: list[Message],
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Response:
        return Response(
            content="Mock response",
            model=model or self.default_model,
            usage=Usage(input_tokens=len(str(messages)), output_tokens=10),
        )

    async def stream(
        self,
        messages: list[Message],
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        for word in ["Mock", " ", "stream", " ", "response"]:
            yield word


class TestAIProvider:
    """AIProvider 추상 클래스 테스트."""

    @pytest.fixture
    def provider(self) -> MockProvider:
        """Mock Provider 인스턴스."""
        return MockProvider()

    def test_name(self, provider: MockProvider):
        """이름 속성."""
        assert provider.name == "mock"

    def test_default_model(self, provider: MockProvider):
        """기본 모델 속성."""
        assert provider.default_model == "mock-model-v1"

    @pytest.mark.asyncio
    async def test_generate(self, provider: MockProvider):
        """generate 메서드."""
        messages = [Message(role="user", content="Hello")]
        response = await provider.generate(messages)

        assert response.content == "Mock response"
        assert response.model == "mock-model-v1"
        assert response.usage.output_tokens == 10

    @pytest.mark.asyncio
    async def test_generate_with_custom_model(self, provider: MockProvider):
        """커스텀 모델로 generate."""
        messages = [Message(role="user", content="Hello")]
        response = await provider.generate(messages, model="custom-model")

        assert response.model == "custom-model"

    @pytest.mark.asyncio
    async def test_stream(self, provider: MockProvider):
        """stream 메서드."""
        messages = [Message(role="user", content="Hello")]
        chunks = []

        async for chunk in provider.stream(messages):
            chunks.append(chunk)

        assert "".join(chunks) == "Mock stream response"

    def test_cannot_instantiate_abstract(self):
        """추상 클래스 직접 인스턴스화 불가."""
        with pytest.raises(TypeError):
            AIProvider()  # type: ignore


class TestProviderInterface:
    """Provider 인터페이스 검증."""

    def test_mock_implements_interface(self):
        """Mock이 인터페이스를 구현하는지 확인."""
        provider = MockProvider()
        assert hasattr(provider, "name")
        assert hasattr(provider, "default_model")
        assert hasattr(provider, "generate")
        assert hasattr(provider, "stream")
        assert callable(provider.generate)
        assert callable(provider.stream)
