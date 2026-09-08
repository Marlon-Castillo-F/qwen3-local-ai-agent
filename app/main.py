from __future__ import annotations

import logging

from app.agent import Agent
from app.client import LlamaClient, ModelConnectionError, ModelResponseError
from app.config import Settings
from app.logging_config import configure_logging
from app.memory import MemoryStore
from app.tools import build_registry


HELP = """Comandos disponibles:
  /info     Estado real del modelo y configuración
  /clear    Limpia el contexto y comienza una sesión nueva
  /history  Muestra el historial de la sesión actual
  /help     Muestra esta ayuda
  /exit     Finaliza el agente"""


def _show_info(client: LlamaClient, settings: Settings) -> None:
    print("\n=== INFORMACIÓN DEL AGENTE ===")
    print(f"Modelo configurado : {settings.model_display_name}")
    print(f"Referencia          : {settings.model_reference}")
    print(f"Motor               : {settings.engine}")
    print(f"API                 : {settings.api_base}")
    print(f"Contexto            : {settings.context_size} tokens")
    print(f"Threads             : {settings.threads}")
    print(f"Workspace           : {settings.workspace}")
    try:
        info = client.model_info()
        print("Estado del modelo   : CONECTADO")
        print(f"Modelo detectado    : {info['detected_model'] or 'sin nombre'}")
    except ModelConnectionError as exc:
        print("Estado del modelo   : DESCONECTADO")
        print(f"Detalle             : {exc}")
    print("==============================\n")


def _show_history(agent: Agent) -> None:
    entries = agent.history()
    if not entries:
        print("\nEl historial de la sesión está vacío.\n")
        return
    print()
    for entry in entries:
        if entry.role == "tool":
            print(f"[tool] {entry.tool_name}")
            print(entry.tool_result or "")
        else:
            label = "Tú" if entry.role == "user" else "IA"
            print(f"{label}> {entry.content}")
    print()


def _print_event(kind: str, value: str) -> None:
    if kind == "tool_call":
        print(f"\n[tool] {value}")
    elif kind == "tool_result":
        print("[tool result]")
        print(value)


def main() -> int:
    settings = Settings()
    settings.ensure_directories()
    logger = configure_logging(settings.logs_dir)
    memory = MemoryStore(settings.memory_db)
    client = LlamaClient(settings, logger=logging.getLogger("ai_agent.client"))
    registry = build_registry(settings)
    agent = Agent(client, registry, memory, settings, logger=logger)

    print("Agente IA local")
    print(f"Modelo: {settings.model_display_name} mediante {settings.engine}")
    print("Escribe /help para ver los comandos.\n")

    try:
        while True:
            try:
                user_input = input("Tú> ").strip()
                if not user_input:
                    continue
                command = user_input.casefold()
                if command in {"/exit", "/quit"}:
                    print("Saliendo...")
                    return 0
                if command == "/clear":
                    agent.clear()
                    print("Contexto limpiado. Nueva sesión iniciada.\n")
                    continue
                if command == "/info":
                    _show_info(client, settings)
                    continue
                if command == "/history":
                    _show_history(agent)
                    continue
                if command == "/help":
                    print(f"\n{HELP}\n")
                    continue
                answer = agent.run(user_input, on_event=_print_event)
                print(f"\nIA> {answer}\n")
            except (ModelConnectionError, ModelResponseError) as exc:
                logger.error("agent_error type=%s detail=%s", type(exc).__name__, exc)
                print(f"\nERROR: {exc}\n")
            except KeyboardInterrupt:
                print("\nSaliendo...")
                return 130
    finally:
        logger.info("session_ended session_id=%s", agent.session_id)
        memory.close()


if __name__ == "__main__":
    raise SystemExit(main())
