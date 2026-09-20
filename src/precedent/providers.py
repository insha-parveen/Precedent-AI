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
