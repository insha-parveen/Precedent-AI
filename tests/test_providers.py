"""Provider contract and behavior unit tests (offline, no live API keys needed)."""
import pytest
from unittest.mock import MagicMock, patch
from src.precedent.providers import (
    ProviderResponse,
    ToolCall,
    TextBlock,
    Usage,
    AnthropicProvider,
    GeminiProvider,
    GrokProvider,
    OpenAIProvider,
    FallbackProvider,
    is_transient_error,
)
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


def test_is_transient_error_detection():
    # Transient errors
    assert is_transient_error(Exception("429 Too Many Requests: quota exceeded")) is True
    assert is_transient_error(Exception("503 Service Unavailable: High demand")) is True
    assert is_transient_error(Exception("ReadTimeout: connection timed out")) is True
    assert is_transient_error(Exception("ResourceExhausted: rate limit reached")) is True
    assert is_transient_error(Exception("WinError 10053 connection reset")) is True

    # Non-transient errors
    assert is_transient_error(ValueError("Invalid argument value")) is False
    assert is_transient_error(TypeError("unsupported operand type")) is False
    assert is_transient_error(KeyError("missing key")) is False
    assert is_transient_error(Exception("401 Unauthorized: invalid_api_key")) is False
    assert is_transient_error(Exception("403 PermissionDenied: access denied")) is False
    assert is_transient_error(Exception("400 Invalid Argument: bad field")) is False


def test_anthropic_provider_contract():
    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client

        # Mock Anthropic message response with text and tool use
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Searching for precedent [doc:123]"

        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.id = "toolu_01"
        tool_block.name = "search_contracts"
        tool_block.input = {"query": "governing law"}

        mock_resp = MagicMock()
        mock_resp.content = [text_block, tool_block]
        mock_resp.usage.input_tokens = 100
        mock_resp.usage.output_tokens = 50
        mock_client.messages.create.return_value = mock_resp

        provider = AnthropicProvider(api_key="sk-ant-test")
        response = provider.create_message(
            system="System prompt",
            messages=[HumanMessage(content="Find governing law")],
            tools=[{"name": "search_contracts", "input_schema": {"type": "object"}}]
        )

        assert isinstance(response, ProviderResponse)
        assert len(response.content) == 1
        assert response.content[0].text == "Searching for precedent [doc:123]"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "search_contracts"
        assert response.tool_calls[0].args == {"query": "governing law"}
        assert response.usage.input_tokens == 100
        assert response.usage.output_tokens == 50


def test_gemini_provider_contract():
    with patch("google.genai.Client") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client

        # Mock Gemini response with text part and function_call part
        text_part = MagicMock()
        text_part.text = "Here is the clause [doc:456]"
        text_part.function_call = None

        fc_part = MagicMock()
        fc_part.text = None
        fc_part.function_call.name = "get_document"
        fc_part.function_call.args = {"document_id": 456}

        candidate = MagicMock()
        candidate.content.parts = [text_part, fc_part]

        mock_resp = MagicMock()
        mock_resp.candidates = [candidate]
        mock_resp.text = "Here is the clause [doc:456]"
        mock_resp.usage_metadata.prompt_token_count = 120
        mock_resp.usage_metadata.candidates_token_count = 45
        mock_client.models.generate_content.return_value = mock_resp

        provider = GeminiProvider(api_key="gemini-test")
        response = provider.create_message(
            system="System prompt",
            messages=[
                HumanMessage(content="Check doc 456"),
                ToolMessage(content="doc text", tool_call_id="call_1", name="get_document")
            ],
            tools=[{"name": "get_document", "input_schema": {"type": "object"}}]
        )

        assert isinstance(response, ProviderResponse)
        assert response.content[0].text == "Here is the clause [doc:456]"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "get_document"
        assert response.tool_calls[0].args == {"document_id": 456}
        assert response.usage.input_tokens == 120
        assert response.usage.output_tokens == 45


def test_grok_openai_provider_contract():
    with patch("openai.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client

        # Mock OpenAI chat completion
        mock_tc = MagicMock()
        mock_tc.id = "call_grok_01"
        mock_tc.function.name = "search_contracts"
        mock_tc.function.arguments = '{"query": "indemnification"}'

        mock_choice = MagicMock()
        mock_choice.message.content = "I will search for indemnification"
        mock_choice.message.tool_calls = [mock_tc]

        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        mock_resp.usage.prompt_tokens = 80
        mock_resp.usage.completion_tokens = 30
        mock_client.chat.completions.create.return_value = mock_resp

        provider = GrokProvider(api_key="grok-test", base_url="https://api.x.ai/v1")
        response = provider.create_message(
            system="System prompt",
            messages=[HumanMessage(content="Find indemnification")],
            tools=[{"name": "search_contracts", "input_schema": {"type": "object"}}]
        )

        assert isinstance(response, ProviderResponse)
        assert response.content[0].text == "I will search for indemnification"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].id == "call_grok_01"
        assert response.tool_calls[0].name == "search_contracts"
        assert response.tool_calls[0].args == {"query": "indemnification"}
        assert response.usage.input_tokens == 80
        assert response.usage.output_tokens == 30


def test_fallback_provider_on_transient_failure():
    primary = MagicMock()
    fallback = MagicMock()

    # Primary raises 503 unavailable
    primary.create_message.side_effect = Exception("503 Service Unavailable: High demand")

    expected_resp = ProviderResponse(
        content=[TextBlock(text="Fallback response [doc:99]")],
        usage=Usage(input_tokens=50, output_tokens=20)
    )
    fallback.create_message.return_value = expected_resp

    fb_provider = FallbackProvider(primary=primary, fallback=fallback)
    result = fb_provider.create_message(
        system="System",
        messages=[{"role": "user", "content": "test"}]
    )

    assert result == expected_resp
    primary.create_message.assert_called_once()
    fallback.create_message.assert_called_once()


def test_fallback_provider_does_not_mask_non_transient_errors():
    primary = MagicMock()
    fallback = MagicMock()

    # Primary raises 401 Unauthorized
    primary.create_message.side_effect = Exception("401 Unauthorized: invalid_api_key")

    fb_provider = FallbackProvider(primary=primary, fallback=fallback)

    with pytest.raises(Exception, match="401 Unauthorized"):
        fb_provider.create_message(
            system="System",
            messages=[{"role": "user", "content": "test"}]
        )

    # Fallback should NOT be called on auth failure
    fallback.create_message.assert_not_called()
