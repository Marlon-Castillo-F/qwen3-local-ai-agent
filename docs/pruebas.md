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
