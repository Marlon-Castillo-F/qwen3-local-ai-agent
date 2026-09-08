# Agente de IA local

Agente Python interactivo para **Qwen3-Coder-30B-A3B-Instruct Q4_K_M** servido por `llama.cpp`. El modelo permanece limitado a `127.0.0.1:8080` y solicita herramientas mediante el formato nativo OpenAI `tool_calls`; Python valida y ejecuta exclusivamente las herramientas registradas.

## Inicio rápido

```bash
cd /home/soporte/ai-agent
source .venv/bin/activate
python -m app.main
```

Comandos: `/info`, `/clear`, `/help`, `/history` y `/exit`.

Herramientas disponibles:

- `list_files`, `read_file` y `write_file`, limitadas a `workspace/`.
- `git_status` y `git_diff`, solo lectura.
- `run_tests`, limitado a `python -m pytest` o `pytest`, sin shell y con timeout.

Ejemplo real validado:

```text
Tú> qué archivos hay disponibles en el workspace usa list_files
[tool] list_files
[tool result]
[DIR] proyecto-demo
[FILE] prueba.txt

IA> En el workspace hay los siguientes elementos:
- Un directorio llamado `proyecto-demo`.
- Un archivo de texto llamado `prueba.txt`.
```

## Servicio del modelo

```bash
systemctl status llama-server.service
sudo systemctl start llama-server.service
sudo systemctl stop llama-server.service
sudo systemctl restart llama-server.service
journalctl -u llama-server.service -f
```

El servicio se ejecuta como el usuario de sistema `llama`, sin shell. El runtime está en `/opt/llama.cpp` y el modelo se presenta en `/var/lib/llama/models/` mediante un enlace duro al blob ya descargado; no se duplicaron 18 GB.

## Pruebas

```bash
.venv/bin/python -m pytest -q
RUN_LIVE_E2E=1 .venv/bin/python -m pytest -q
```

Última validación completa, 2026-09-08: `32 passed in 25.59s`.

## Datos locales

- Memoria: `data/memory.db` (SQLite; ignorada por Git).
- Logs: `logs/agent.log` (rotación 5 MB, tres copias; ignorados por Git).
- Workspace autorizado: `/home/soporte/ai-agent/workspace`.
- Backup previo: `/home/soporte/ai-agent-backups/ai-agent-pre-mvp-20260908T1535Z.tar.gz`.

La clave SSH temporal `codex-ai-agent-temporary-2026-09-08` sigue instalada hasta que se confirme el cierre del trabajo remoto.

Consulta los detalles en [`docs/arquitectura.md`](docs/arquitectura.md), [`docs/seguridad.md`](docs/seguridad.md) y [`docs/pruebas.md`](docs/pruebas.md).
