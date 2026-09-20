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
