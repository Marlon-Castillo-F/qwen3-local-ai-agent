# Pruebas

## Ejecuciones realizadas

Primera suite tras instalar el código:

```text
27 passed, 2 failed, 2 skipped
```

Los dos fallos revelaron que `ChatResponse.content` no aceptaba el caso vacío de una respuesta compuesta únicamente por tool calls. Se corrigió y se repitió la suite:

```text
29 passed, 2 skipped in 0.47s
```

Después de añadir censura de secretos:

```text
30 passed, 2 skipped in 0.52s
```

Suite de seguridad separada:

```text
18 passed in 0.10s
```

Suite completa con integración, antes de systemd:

```text
32 passed in 14.90s
```

Instancia manual no-root en 8081:

```text
2 passed in 35.86s
```

Instancia manual no-root en 8080:

```text
2 passed in 25.40s
```

Suite final contra systemd:

```text
32 passed in 25.59s
```

## Resultados end-to-end exactos

Listado:

```text
[tool] list_files
[tool result]
[DIR] proyecto-demo
[FILE] prueba.txt

IA> En el workspace hay los siguientes elementos:
- Un directorio llamado `proyecto-demo`.
- Un archivo de texto llamado `prueba.txt`.
```

Lectura:

```text
[tool] read_file
[tool result]
Servidor de IA local

IA> El contenido exacto del archivo `prueba.txt` es:
Servidor de IA local
```

Las pruebas comprueban el evento de tool call, el resultado real y que la respuesta final contiene los datos observados.

## Cobertura de seguridad

- Path traversal relativo y rutas absolutas.
- Escape mediante symlink, tanto en lectura como escritura.
- Archivo inexistente.
- Archivo binario.
- Archivo o contenido por encima del máximo.
- Escritura válida y atómica dentro del workspace.
- Herramienta no registrada.
- JSON inválido, tipo incorrecto, argumentos faltantes y adicionales.
- Timeout de procesos.
- Allowlist de `run_tests` y ausencia de `shell=True`.
- `git_status` y `git_diff` sobre un repositorio real temporal.
- Memoria SQLite, `/history`, `/info` y error de conexión.
- Censura de secretos evidentes.

Para ejecutar:

```bash
.venv/bin/python -m pytest -q
RUN_LIVE_E2E=1 .venv/bin/python -m pytest -q
```

## Validación posterior al reinicio

Validación completada el `2026-09-08T17:20:53+00:00`.

- Ubuntu inició a las `2026-09-08 17:16:24 UTC`, kernel `6.8.0-139-generic`, con `boot_id=d251b50a-a48e-43e2-af56-cbda9cd1b46b`.
- `llama-server.service` apareció `enabled` y `active` sin intervención manual y quedó saludable tras terminar de cargar el modelo.
- Existía exactamente una instancia, PID 1434, ejecutada por el usuario `llama` con PPID 1.
- Socket exclusivo: `127.0.0.1:8080`.
- `/health`: `{"status":"ok"}`.
- `/v1/models`: `lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M`.
- `list_files` produjo un tool call real y devolvió `[DIR] proyecto-demo` y `[FILE] prueba.txt`; Qwen utilizó ambos nombres en su respuesta.
- `read_file` produjo un tool call real, devolvió `Servidor de IA local` y Qwen utilizó ese contenido en su respuesta.
- Suite completa live: `32 passed in 13.54s`; cero fallos y cero omisiones.
- Git estaba limpio antes de esta actualización documental.
- La clave `codex-ai-agent-temporary-2026-09-08` fue eliminada: conteo antes `1`, después `0`. El backup es `/home/soporte/.ssh/authorized_keys.pre-codex-removal-20260908T171511Z.bak`.
- La reconexión posterior utilizó autenticación normal por contraseña con `PubkeyAuthentication=no`.
