# Pruebas

## Suite

La suite utiliza pytest y cubre lógica aislada, integración entre componentes y dos escenarios live contra Qwen servido por llama.cpp.

```bash
# Unitarias e integración local; las pruebas live se omiten
python -m pytest -q

# Suite completa con llama-server disponible en localhost
RUN_LIVE_E2E=1 python -m pytest -q
```

## Cobertura principal

- `list_files`, `read_file` y `write_file`.
- Path traversal relativo y rutas absolutas.
- Escape mediante symlink en lectura y escritura.
- Archivo inexistente, binario o demasiado grande.
- Escritura válida, anidada y atómica.
- Herramienta no registrada.
- JSON inválido, tipos incorrectos, campos faltantes y argumentos adicionales.
- Allowlist de `run_tests`, ausencia de `shell=True` y timeout.
- `git_status` y `git_diff` sobre un repositorio temporal real.
- Memoria SQLite, separación de sesiones y censura básica de secretos.
- `/info`, `/help`, `/history`, `/clear` y `/exit`.
- Respuestas y errores del cliente HTTP.
- Ciclo agentic con mensajes `role=tool`.
- Indexación y retrieval SQLite FTS5, incluidos términos DBA en español.
- Parsers de `STATISTICS IO`, `STATISTICS TIME`, `.sqlplan` y deadlock XML.
- Seguridad y validación de argumentos de herramientas DBA.
- Gate que oculta analizadores de archivos cuando el usuario no aporta una extensión compatible.

## Evolución de la validación

La primera ejecución después de instalar la implementación produjo:

```text
27 passed, 2 failed, 2 skipped
```

Los dos fallos mostraron un caso válido no contemplado: una respuesta que contiene solo `tool_calls` puede traer `content` vacío. Se corrigió `ChatResponse` y todas las ejecuciones posteriores pasaron.

La suite específica de seguridad obtuvo:

```text
18 passed in 0.10s
```

La validación completa previa al servicio obtuvo:

```text
32 passed in 14.90s
```

También se ejecutaron ambas pruebas live contra una instancia manual no-root en un puerto alternativo y, después, en el puerto final. Ambas pasaron antes de crear la unidad systemd.

La validación final de DBA Edition obtuvo:

```text
62 passed, 2 skipped in 0.68s
```

Las dos omisiones son exclusivamente los casos live protegidos por `RUN_LIVE_E2E`. Con llama-server disponible se ejecutó la suite completa:

```text
64 passed in 22.85s
0 failed
```

## Resultados end-to-end

### Listado

```text
[tool] list_files
[tool result]
[DIR] proyecto-demo
[FILE] prueba.txt
```

La prueba comprueba el evento `tool_call`, los nombres del resultado real y que la respuesta final de Qwen los utilice.

### Lectura

```text
[tool] read_file
[tool result]
Servidor de IA local
```

La prueba comprueba que Qwen solicite `read_file`, que Python devuelva el contenido y que el texto final incluya ese marcador real.

## Validación posterior al reboot

Validación completada el 8 de septiembre de 2026:

- Ubuntu inició con kernel `6.8.0-139-generic`.
- `llama-server.service` apareció `enabled` y `active` sin intervención manual.
- Existía exactamente una instancia, propiedad del usuario `llama` y con systemd como padre.
- Socket exclusivo: `127.0.0.1:8080`.
- `/health`: `{"status":"ok"}`.
- `/v1/models`: `lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M`.
- `list_files` y `read_file` produjeron tool calls reales después del reboot.
- Resultado final: `32 passed in 13.54s`, cero fallos y cero omisiones.
- La credencial temporal de mantenimiento fue retirada y la reconexión normal fue verificada.

No se incluyen identificadores de host, credenciales ni datos de autenticación en este documento.
