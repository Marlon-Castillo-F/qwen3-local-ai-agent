# Seguridad

## Límites del agente

- El agente se ejecuta manualmente como `soporte`, nunca como root.
- Las rutas del modelo deben ser relativas a `workspace/`.
- Se bloquean rutas absolutas, path traversal y cualquier componente symlink.
- Lecturas limitadas a 1 MiB, UTF-8 y sin bytes nulos.
- Escrituras atómicas, UTF-8 y limitadas a 1 MiB.
- Herramientas registradas explícitamente; nombres desconocidos se rechazan.
- Argumentos validados por tipo, campos requeridos, enumeraciones y campos adicionales.
- Git es solo lectura.
- `run_tests` usa listas de argumentos, nunca `shell=True`, y aplica timeout.
- SQLite censura patrones evidentes de contraseñas, tokens, bearer tokens y claves privadas.
- Los logs no incluyen prompts, argumentos completos ni resultados de archivos.

La detección de secretos es defensiva, no infalible; no deben introducirse secretos en conversaciones ni almacenarse dentro del workspace.

## Servicio del modelo

- Usuario de sistema `llama`, UID 999, shell `/usr/sbin/nologin`.
- Socket exclusivo `127.0.0.1:8080`.
- CORS limitado a localhost.
- Sin capacidades Linux y con `NoNewPrivileges=true`.
- `ProtectSystem=strict`, `ProtectHome=true`, dispositivos privados y `/proc` restringido.
- Única ruta escribible: `/var/lib/llama/cache`.
- Reinicio `on-failure`, espera 10 segundos y límites de arranque.

`systemd-analyze security llama-server.service` reportó exposición `3.6 OK` el 2026-09-08. El servicio no necesita acceder a `/root`.

## Modelo sin duplicación

El archivo de `/var/lib/llama/models` es un enlace duro al blob existente: ambos mostraron `device=64512`, `inode=2363871`, `links=2` y tamaño `18632186176`. El inode quedó `root:llama 0640`; `/root` continúa `0700` y no se abrió al servicio.

## Clave SSH temporal

La clave comentada `codex-ai-agent-temporary-2026-09-08` debe retirarse de `/home/soporte/.ssh/authorized_keys` cuando termine el trabajo remoto.
