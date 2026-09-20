from typing import Protocol, Any, List, Optional, Dict
from dataclasses import dataclass, field
import json
import logging
import re
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

        response = self.client.models.generate_content(
            model=model or "gemini-3.1-flash-lite",
            contents=contents,
            config=config
        )

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
