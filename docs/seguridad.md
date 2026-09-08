# Seguridad

El modelo se trata como una fuente de solicitudes no confiables. Ninguna afirmación textual ni tool call se considera autorización para ejecutar una acción.

## Controles del agente

### Registro y argumentos

- Todas las herramientas se registran explícitamente mediante `ToolSpec`.
- Un nombre desconocido se rechaza antes de buscar o ejecutar código.
- Los argumentos deben ser un objeto JSON y respetar tipos, campos requeridos, enumeraciones y `additionalProperties`.
- El resultado se limita antes de volver al contexto del modelo.

### Archivos

- Todas las rutas deben ser relativas a `workspace/`.
- Se bloquean rutas absolutas, path traversal y componentes symlink.
- Las lecturas aceptan únicamente archivos regulares UTF-8 de hasta 1 MiB.
- Los bytes nulos y datos no decodificables se consideran binarios.
- Las escrituras tienen el mismo límite y usan reemplazo atómico.
- La comprobación de la ruta se repite después de preparar el directorio padre.

### Procesos y Git

- `git_status` y `git_diff` no modifican el repositorio.
- `run_tests` solo acepta `python -m pytest` o `pytest`.
- `subprocess.run` recibe una lista de argumentos y nunca usa `shell=True`.
- Git y pytest tienen timeout; el modelo no puede añadir flags o comandos libres.

### Persistencia y logs

- SQLite censura patrones evidentes de contraseñas, tokens bearer, API keys y bloques de clave privada.
- Los logs registran nombres, estados, tamaños, errores y duraciones; no guardan prompts ni resultados completos de archivos.
- La censura es heurística. Los usuarios no deben introducir secretos ni almacenarlos en el workspace.

## Controles de llama-server

- Usuario de sistema dedicado `llama`, sin shell y sin privilegios administrativos.
- API enlazada exclusivamente a `127.0.0.1:8080`.
- CORS limitado a localhost y UI deshabilitada.
- `NoNewPrivileges=true` y conjunto de capacidades vacío.
- `ProtectSystem=strict`, `ProtectHome=true`, dispositivos privados y `/proc` restringido.
- La única ruta de escritura declarada para el servicio es su caché.
- Reinicio `on-failure` con espera y límites de arranque.

`systemd-analyze security` reportó una exposición `3.6 OK` para la unidad validada. Es una ayuda de auditoría, no una certificación de seguridad.

## Modelo sin duplicación ni acceso a `/root`

El modelo visible en `/var/lib/llama/models/` comparte inode con el blob descargado mediante un enlace duro. El archivo está restringido a `root:llama 0640`, mientras `/root` permanece cerrado al usuario del servicio. El runtime de `/opt/llama.cpp` es propiedad de root y no es modificable por `llama`.

## Cierre de acceso de mantenimiento

La credencial SSH temporal utilizada durante la implementación se retiró después de crear un backup y completar el reboot de validación. La reconexión final se comprobó mediante el mecanismo normal del servidor. No se incluyen claves, huellas, contraseñas ni contenido de `authorized_keys` en este repositorio.

## Alcance

Estos controles son adecuados para un agente local de laboratorio. Antes de exponerlo a otros usuarios o redes se necesitarían, como mínimo, autenticación, políticas de autorización, aislamiento adicional, revisión de datos y observabilidad centralizada.
