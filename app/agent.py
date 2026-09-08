from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from typing import Any

from app.client import LlamaClient, ModelResponseError
from app.config import SYSTEM_PROMPT, Settings
from app.memory import MemoryEntry, MemoryStore
from app.tools.base import ToolError, ToolRegistry


EventCallback = Callable[[str, str], None]


class Agent:
    def __init__(
        self,
        client: LlamaClient,
        registry: ToolRegistry,
        memory: MemoryStore,
        settings: Settings,
        *,
        logger: logging.Logger | None = None,
    ):
        self.client = client
        self.registry = registry
        self.memory = memory
        self.settings = settings
        self.logger = logger or logging.getLogger("ai_agent.agent")
        self.session_id = ""
        self.messages: list[dict[str, Any]] = []
        self.clear()

    def clear(self) -> None:
        self.session_id = str(uuid.uuid4())
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.logger.info("session_started session_id=%s", self.session_id)

    def history(self) -> list[MemoryEntry]:
        return self.memory.history(self.session_id)

    def run(self, user_input: str, on_event: EventCallback | None = None) -> str:
        on_event = on_event or (lambda _kind, _value: None)
        self.messages.append({"role": "user", "content": user_input})
        self.memory.add(self.session_id, "user", user_input)

        for _round in range(self.settings.max_tool_rounds + 1):
            response = self.client.chat(self.messages, self.registry.schemas())
            if not response.tool_calls:
                if not response.content.strip():
                    raise ModelResponseError("El modelo devolvió una respuesta vacía")
                self.messages.append(
                    {"role": "assistant", "content": response.content}
                )
                self.memory.add(self.session_id, "assistant", response.content)
                return response.content

            assistant_message: dict[str, Any] = {
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [call.as_openai_dict() for call in response.tool_calls],
            }
            self.messages.append(assistant_message)
            if response.content:
                self.memory.add(self.session_id, "assistant", response.content)

            for call in response.tool_calls:
                on_event("tool_call", call.name)
                self.logger.info(
                    "tool_requested session_id=%s name=%s", self.session_id, call.name
                )
                try:
                    result = self.registry.execute(call.name, call.arguments)
                except ToolError as exc:
                    result = f"ERROR: {exc}"
                on_event("tool_result", result)
                self.memory.add(
                    self.session_id,
                    "tool",
                    "",
                    tool_name=call.name,
                    tool_result=result,
                )
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.name,
                        "content": result,
                    }
                )

        raise ModelResponseError(
            f"Se alcanzó el límite de {self.settings.max_tool_rounds} rondas de herramientas"
        )
