import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock


class TestLLMRoutes:
    """Test cases for LLM API routes."""

    @pytest.mark.asyncio
    async def test_sync_chat(self, client: AsyncClient):
        """Test synchronous chat endpoint."""
        with patch("src.routers.llm.chain") as mock_chain:
            mock_chain.invoke.return_value = "Mocked response"

            response = await client.get(
                "/llm/sync/chat",
                params={"query": "Hello, world!"}
            )

            assert response.status_code == 200
            assert response.json() == "Mocked response"
            mock_chain.invoke.assert_called_once_with({"query": "Hello, world!"})

    @pytest.mark.asyncio
    async def test_async_chat(self, client: AsyncClient):
        """Test asynchronous chat endpoint."""
        with patch("src.routers.llm.chain") as mock_chain:
            mock_chain.ainvoke = AsyncMock(return_value="Async mocked response")

            query_data = {
                "prompt": "Test prompt",
                "min_length": 3,
                "max_tokens": 50
            }

            response = await client.get(
                "/llm/async/chat",
                params=query_data
            )

            assert response.status_code == 200
            assert response.json() == "Async mocked response"
            mock_chain.ainvoke.assert_called_once_with({"query": "Test prompt"})

    @pytest.mark.asyncio
    async def test_async_chat_stream(self, client: AsyncClient):
        """Test asynchronous streaming chat endpoint."""
        with patch("src.routers.llm.client") as mock_client:
            # Mock streaming response
            mock_stream = MagicMock()
            mock_event = MagicMock()
            mock_event.type = "content.delta"
            mock_event.delta = "test"

            mock_stream.__enter__ = MagicMock(return_value=mock_stream)
            mock_stream.__exit__ = MagicMock(return_value=False)
            mock_stream.__iter__ = MagicMock(return_value=iter([mock_event]))

            mock_client.chat.completions.stream.return_value = mock_stream

            response = await client.get(
                "/llm/async/chat-stream",
                params={"query": "Stream test"}
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    @pytest.mark.asyncio
    async def test_async_generate_text(self, client: AsyncClient):
        """Test asynchronous text generation endpoint."""
        with patch("src.routers.llm.client") as mock_client:
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Generated text content"
            mock_response.choices = [mock_choice]

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            response = await client.get(
                "/llm/async/generate-text",
                params={"query": "Generate something"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["text"] == "Generated text content"

            mock_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["model"] == "gpt-4o-mini"
            assert call_kwargs["messages"][0]["content"] == "Generate something"

    @pytest.mark.asyncio
    async def test_async_generate_text_error(self, client: AsyncClient):
        """Test text generation endpoint with error."""
        with patch("src.routers.llm.client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("API Error")
            )

            response = await client.get(
                "/llm/async/generate-text",
                params={"query": "Test query"}
            )

            assert response.status_code == 500
            assert "API Error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_complete_text(self, client: AsyncClient):
        """Test text completion endpoint."""
        with patch("src.routers.llm.llm") as mock_llm:
            mock_llm.return_value = "Completion result"

            response = await client.get(
                "/llm/complete",
                params={"prompt": "Complete this"}
            )

            assert response.status_code == 200
            assert response.json() == "Completion result"
            mock_llm.assert_called_once_with("Complete this")

    @pytest.mark.asyncio
    async def test_async_chat_validation(self, client: AsyncClient):
        """Test async chat with invalid data validation."""
        # Missing required prompt field
        response = await client.get("/llm/async/chat")

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_multiple_llm_calls(self, client: AsyncClient):
        """Test making multiple LLM calls in sequence."""
        with patch("src.routers.llm.chain") as mock_chain:
            mock_chain.invoke.side_effect = ["Response 1", "Response 2", "Response 3"]

            queries = ["Query 1", "Query 2", "Query 3"]
            responses = []

            for query in queries:
                response = await client.get(
                    "/llm/sync/chat",
                    params={"query": query}
                )
                responses.append(response.json())

            assert len(responses) == 3
            assert responses[0] == "Response 1"
            assert responses[1] == "Response 2"
            assert responses[2] == "Response 3"
            assert mock_chain.invoke.call_count == 3
