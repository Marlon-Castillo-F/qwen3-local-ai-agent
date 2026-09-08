# Arquitectura

## Flujo agentic

```text
Usuario
  -> app.main (CLI y comandos)
  -> Agent.run
  -> LlamaClient /v1/chat/completions + esquemas tools
  -> Qwen devuelve tool_calls
  -> ToolRegistry valida nombre y argumentos
  -> handler seguro ejecuta la operación real
  -> resultado role=tool vuelve a Qwen
  -> Qwen redacta la respuesta final
```

No existe ejecución por nombre dinámico, `eval`, importación decidida por el modelo ni shell libre.

## Componentes

- `app/main.py`: CLI y comandos especiales.
- `app/agent.py`: ciclo de herramientas, límite de rondas e historial.
- `app/client.py`: cliente HTTP OpenAI compatible y consulta real de `/v1/models`.
- `app/config.py`: configuración, rutas y system prompt.
- `app/models.py`: estructuras de respuestas y tool calls.
- `app/memory.py`: persistencia SQLite con censura básica de secretos.
- `app/logging_config.py`: logging rotativo.
- `app/tools/base.py`: registro explícito y validación de JSON.
- `app/tools/files.py`: archivos limitados al workspace.
- `app/tools/git_tools.py`: consultas Git sin mutaciones.
- `app/tools/test_tools.py`: pytest con allowlist y timeout.

## Directorios

```text
/home/soporte/ai-agent/
├── app/
│   └── tools/
├── data/
├── deploy/
├── docs/
├── logs/
├── reports/
├── tests/
├── workspace/
├── requirements.txt
├── pytest.ini
└── README.md
```

## Inferencia

`llama-server.service` ejecuta `/opt/llama.cpp/build/bin/llama-server` como `llama`. El modelo se abre desde `/var/lib/llama/models/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf`, con alias API estable, 24 threads, 24 batch threads, contexto 8192 y un slot.
