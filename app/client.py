from __future__ import annotations

import logging
import time
from typing import Any

import requests

from app.config import Settings
from app.models import ChatResponse, ToolCall


class ModelConnectionError(RuntimeError):
    pass


class ModelResponseError(RuntimeError):
    pass


class LlamaClient:
    def __init__(
        self,
        settings: Settings,
        *,
        session: requests.Session | None = None,
        logger: logging.Logger | None = None,
    ):
        self.settings = settings
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger("ai_agent.client")

    def model_info(self) -> dict[str, Any]:
        try:
            response = self.session.get(
                f"{self.settings.api_base}/v1/models", timeout=5
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise ModelConnectionError(
                f"No se pudo consultar llama-server: {exc}"
            ) from exc

        models = payload.get("data") or payload.get("models") or []
        detected = None
        if models:
            detected = (
                models[0].get("id")
                or models[0].get("name")
                or models[0].get("model")
            )
        return {"connected": True, "detected_model": detected, "raw": payload}

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ChatResponse:
        payload = {
            "model": self.settings.model_reference,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "parallel_tool_calls": False,
            "temperature": 0.2,
            "max_tokens": 1024,
        }
        started = time.monotonic()
        self.logger.info(
            "model_request messages=%d tools=%d", len(messages), len(tools)
        )
        try:
            response = self.session.post(
                f"{self.settings.api_base}/v1/chat/completions",
                json=payload,
                timeout=self.settings.request_timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.Timeout as exc:
            self.logger.error("model_timeout duration=%.3fs", time.monotonic() - started)
            raise ModelConnectionError("El modelo agotó el tiempo de espera") from exc
        except (requests.RequestException, ValueError) as exc:
            self.logger.error(
                "model_error duration=%.3fs type=%s",
                time.monotonic() - started,
                type(exc).__name__,
            )
            raise ModelConnectionError(f"Error consultando llama-server: {exc}") from exc

        try:
            choice = data["choices"][0]
            message = choice["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelResponseError("Respuesta inválida de llama-server") from exc

        calls: list[ToolCall] = []
        for raw_call in message.get("tool_calls") or []:
            function = raw_call.get("function") or {}
            calls.append(
                ToolCall(
                    id=str(raw_call.get("id") or f"call_{len(calls)}"),
                    name=str(function.get("name") or ""),
                    arguments=function.get("arguments") or "{}",
                )
            )

        duration = time.monotonic() - started
        self.logger.info(
            "model_response duration=%.3fs finish_reason=%s tool_calls=%d",
            duration,
            choice.get("finish_reason", ""),
            len(calls),
        )
        return ChatResponse(
            content=message.get("content") or "",
            tool_calls=calls,
            finish_reason=choice.get("finish_reason") or "",
            model=data.get("model") or "",
            usage=data.get("usage") or {},
        )
