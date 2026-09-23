from typing import Protocol, Any, List, Optional, Dict
from dataclasses import dataclass, field
import json
import logging
import re
import time
from .config import settings

logger = logging.getLogger(__name__)

@dataclass
class ToolCall:
    id: str
    name: str
    args: dict

@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

@dataclass
class TextBlock:
    text: str

@dataclass
class ProviderResponse:
    content: list[TextBlock] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    raw_response: Any = None

class LLMProvider(Protocol):
    def create_message(
        self,
        system: str,
        messages: list[Any],
        tools: list[dict] | None = None,
        model: str | None = None
    ) -> ProviderResponse:
        ...

import anthropic
from google import genai

class GeminiProvider:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key or "dummy-key")

    def create_message(
        self,
        system: str,
        messages: list[Any],
        tools: list[dict] | None = None,
        model: str | None = None
    ) -> ProviderResponse:
        contents = []
        for m in messages:
            if hasattr(m, "type"):
                m_type = getattr(m, "type", "")
                m_content = getattr(m, "content", "")
                # Check for cached native candidate
                raw_cand = getattr(m, "additional_kwargs", {}).get("gemini_candidate")
                if raw_cand is not None:
                    contents.append(raw_cand.content)
                    continue

                if m_type in ("human", "user"):
                    contents.append(genai.types.Content(
                        role="user",
                        parts=[genai.types.Part.from_text(text=str(m_content))]
                    ))
                elif m_type == "tool":
                    tool_name = None
                    if contents and contents[-1].role == "model" and contents[-1].parts:
                        for p in contents[-1].parts:
                            if hasattr(p, "function_call") and p.function_call:
                                tool_name = p.function_call.name
                                break
                    if not tool_name:
                        tool_name = getattr(m, "name", "tool") or "tool"
                        if ":" in tool_name:
                            tool_name = tool_name.split(":")[-1]

                    contents.append(genai.types.Content(
                        role="user",
                        parts=[genai.types.Part.from_function_response(
                            name=tool_name,
                            response={"result": str(m_content)}
                        )]
                    ))
                elif m_type in ("ai", "assistant"):
                    parts = []
                    if m_content:
                        parts.append(genai.types.Part.from_text(text=str(m_content)))
                    if hasattr(m, "tool_calls") and m.tool_calls:
                        for tc in m.tool_calls:
                            parts.append(genai.types.Part.from_function_call(
                                name=tc["name"],
                                args=tc.get("args", {})
                            ))
                    if parts:
                        contents.append(genai.types.Content(role="model", parts=parts))
            elif isinstance(m, dict):
                role = m.get("role", "user")
                content = m.get("content", "")
                contents.append(genai.types.Content(
                    role="user" if role in ("user", "human") else "model",
                    parts=[genai.types.Part.from_text(text=str(content))]
                ))

        if not contents:
            contents = [genai.types.Content(
                role="user",
                parts=[genai.types.Part.from_text(text="Hello")]
            )]

        function_declarations = None
        if tools:
            function_declarations = []
            for tool in tools:
                if "input_schema" in tool:
                    schema = tool["input_schema"]
                    func_decl = {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": {
                            "type": schema.get("type", "object"),
                            "properties": schema.get("properties", {}),
                            "required": schema.get("required", [])
                        }
                    }
                    function_declarations.append(func_decl)

        config = genai.types.GenerateContentConfig(
            system_instruction=system,
        )
        if function_declarations:
            config.tools = [{"function_declarations": function_declarations}]

        response = None
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = self.client.models.generate_content(
                    model=model or "gemini-3.1-flash-lite",
                    contents=contents,
                    config=config
                )
                break
            except Exception as exc:
                if is_transient_error(exc) and attempt < max_attempts - 1:
                    logger.warning(
                        f"Gemini generate_content transient error: {exc}. "
                        f"Retrying attempt {attempt + 2}/{max_attempts}..."
                    )
                    time.sleep(2.0 * (attempt + 1))
                    continue
                raise exc

        content_items = []
        tool_calls = []
        candidate = response.candidates[0] if response.candidates else None

        if candidate and candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    content_items.append(TextBlock(text=part.text))
                elif hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    tool_calls.append(ToolCall(
                        id=f"call_{len(tool_calls)}",
                        name=fc.name,
                        args=dict(fc.args) if fc.args else {}
                    ))

        if not content_items and not tool_calls and response.text:
            content_items.append(TextBlock(text=response.text))

        in_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
        out_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0

        return ProviderResponse(
            content=content_items,
            tool_calls=tool_calls,
            usage=Usage(input_tokens=in_tokens, output_tokens=out_tokens),
            raw_response=candidate
        )

class AnthropicProvider:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key or "sk-ant-dummy")

    def create_message(
        self,
        system: str,
        messages: list[Any],
        tools: list[dict] | None = None,
        model: str | None = None
    ) -> ProviderResponse:
        formatted = []
        for m in messages:
            if hasattr(m, "type"):
                if m.type in ("human", "user"):
                    formatted.append({"role": "user", "content": m.content})
                elif m.type == "tool":
                    formatted.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": getattr(m, "tool_call_id", "tool_call"),
                            "content": m.content,
                        }]
                    })
                elif m.type in ("ai", "assistant"):
                    blocks = []
                    if m.content:
                        blocks.append({"type": "text", "text": m.content})
                    if hasattr(m, "tool_calls") and m.tool_calls:
                        for tc in m.tool_calls:
                            blocks.append({
                                "type": "tool_use",
                                "id": tc.get("id", "call_0"),
                                "name": tc.get("name"),
                                "input": tc.get("args", {}),
                            })
                    formatted.append({"role": "assistant", "content": blocks or m.content})
            elif isinstance(m, dict):
                formatted.append(m)

        resp = self.client.messages.create(
            model=model or settings.agent_model,
            system=system,
            messages=formatted,
            tools=tools,
            max_tokens=1500
        )

        content_items = []
        tool_calls = []
        for block in resp.content:
            if block.type == "text":
                content_items.append(TextBlock(text=block.text))
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(id=block.id, name=block.name, args=block.input))

        return ProviderResponse(
            content=content_items,
            tool_calls=tool_calls,
            usage=Usage(
                input_tokens=resp.usage.input_tokens,
                output_tokens=resp.usage.output_tokens
            ),
            raw_response=resp
        )

import openai

class GrokProvider:
    """Provider for xAI Grok or OpenAI-compatible endpoints."""
    def __init__(self, api_key: str, base_url: str | None = None):
        self.client = openai.OpenAI(
            api_key=api_key or settings.grok_api_key or settings.openai_api_key or "dummy-key",
            base_url=base_url or settings.grok_base_url
        )

    def create_message(
        self,
        system: str,
        messages: list[Any],
        tools: list[dict] | None = None,
        model: str | None = None
    ) -> ProviderResponse:
        formatted = [{"role": "system", "content": system}]
        for m in messages:
            if hasattr(m, "type"):
                if m.type in ("human", "user"):
                    formatted.append({"role": "user", "content": str(m.content)})
                elif m.type == "tool":
                    formatted.append({
                        "role": "tool",
                        "tool_call_id": getattr(m, "tool_call_id", "call_0"),
                        "content": str(m.content)
                    })
                elif m.type in ("ai", "assistant"):
                    msg_dict: dict[str, Any] = {"role": "assistant"}
                    if m.content:
                        msg_dict["content"] = str(m.content)
                    if hasattr(m, "tool_calls") and m.tool_calls:
                        msg_dict["tool_calls"] = [
                            {
                                "id": tc.get("id", f"call_{i}"),
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc.get("args", {}))
                                }
                            }
                            for i, tc in enumerate(m.tool_calls)
                        ]
                    formatted.append(msg_dict)
            elif isinstance(m, dict):
                formatted.append(m)

        openai_tools = None
        if tools:
            openai_tools = []
            for t in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t.get("input_schema", {"type": "object", "properties": {}})
                    }
                })

        kwargs: dict[str, Any] = {
            "model": model or settings.grok_model,
            "messages": formatted
        }
        if openai_tools:
            kwargs["tools"] = openai_tools

        response = self.client.chat.completions.create(**kwargs)
        choice = response.choices[0].message

        content_items = []
        if choice.content:
            content_items.append(TextBlock(text=choice.content))

        tool_calls = []
        if choice.tool_calls:
            for tc in choice.tool_calls:
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except Exception:
                    args = {}
                tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, args=args))

        in_tokens = response.usage.prompt_tokens if response.usage else 0
        out_tokens = response.usage.completion_tokens if response.usage else 0

        return ProviderResponse(
            content=content_items,
            tool_calls=tool_calls,
            usage=Usage(input_tokens=in_tokens, output_tokens=out_tokens),
            raw_response=response
        )

# OpenAIProvider alias for generic OpenAI endpoints
OpenAIProvider = GrokProvider

def is_transient_error(exc: Exception) -> bool:
    """Identify if an error is transient (e.g. rate limit, 503 unavailable, network timeout)
    rather than a permanent configuration, bad request, authentication, or programming error.
    """
    msg = str(exc).lower()
    # Explicit non-transient errors
    if isinstance(exc, (ValueError, TypeError, KeyError, AttributeError, SyntaxError)):
        return False
    if "401" in msg or "invalid_api_key" in msg or "authentication" in msg or "unauthorized" in msg:
        return False
    if "403" in msg or "permission_denied" in msg:
        return False
    if "400" in msg and "invalid_argument" in msg and "thought_signature" not in msg:
        return False

    # Transient error indicators
    if "429" in msg or "resource_exhausted" in msg or "rate limit" in msg or "quota" in msg:
        return True
    if "503" in msg or "unavailable" in msg or "high demand" in msg or "overloaded" in msg:
        return True
    if "500" in msg or "502" in msg or "504" in msg or "internal server error" in msg or "bad gateway" in msg:
        return True
    if "timeout" in msg or "connection" in msg or "network" in msg or "winerror 10053" in msg or "winerror 1225" in msg:
        return True

    return False

class FallbackProvider:
    def __init__(self, primary: LLMProvider, fallback: LLMProvider):
        self.primary = primary
        self.fallback = fallback

    def create_message(
        self,
        system: str,
        messages: list[Any],
        tools: list[dict] | None = None,
        model: str | None = None
    ) -> ProviderResponse:
        try:
            return self.primary.create_message(system, messages, tools, model)
        except Exception as exc:
            if is_transient_error(exc):
                logger.warning(f"Primary provider failed with transient error: {exc}. Falling back.")
                return self.fallback.create_message(system, messages, tools, model)
            # Re-raise non-transient errors (auth, programming, invalid arguments)
            raise exc
